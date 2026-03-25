import logging
from collections import defaultdict
from typing import Any

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

# Department
class Department(models.Model):
    """Management of university departments."""
    _name = 'university.department'
    _inherit = ['batch.count.mixin']
    _description = 'Department'

    name = fields.Char(string='Name', required=True, index=True, help="Name of the department.")
    university_id = fields.Many2one('university.university', string='University', required=True, index=True)
    manager_id = fields.Many2one(
        'university.professor',
        string='Manager',
        index=True,
        domain="[('department_id', '=', id)]",
    )
    professor_ids = fields.One2many('university.professor', 'department_id', string='Professors')


    professor_count = fields.Integer(compute='_compute_counts', string='Professor Count')

    @api.depends('professor_ids')
    def _compute_counts(self) -> None:
        """Calculates the total number of professors recursively in bulk."""
        counts = self._get_batch_counts('university.professor', 'department_id')
        for record in self:
            record.professor_count = counts.get(record.id, 0)

    @api.constrains('manager_id')
    def _check_manager_belongs_to_department(self) -> None:
        """
        Validates that the department manager belongs to this department.

        Raises:
            ValidationError: If the manager is not a professor of this department.
        """
        for record in self:
            if record.manager_id and record.manager_id.department_id != record:
                raise ValidationError(_(
                    "The manager '%(manager)s' must belong to this department. "
                    "Only professors assigned to this department can be selected as manager.",
                    manager=record.manager_id.name,
                ))

# Professor
class UniversityProfessor(models.Model):
    """Management of university professors."""
    _name = 'university.professor'
    _inherit = ['image.mixin', 'batch.count.mixin', 'website.published.mixin', 'website.seo.metadata']
    _description = 'University Professor'

    name = fields.Char(string='Name', required=True, index=True)
    email = fields.Char(string='Email', index=True)
    
    university_id = fields.Many2one('university.university', string='University', required=True, index=True)
    department_id = fields.Many2one(
        'university.department',
        string='Department',
        required=True,
        index=True,
        ondelete='cascade',
        domain="[('university_id', '=', university_id)]",
    )
    subject_ids = fields.Many2many(
        'university.subject', 
        string='Subjects',
        domain="[('university_id', '=', university_id)]"
    )

    enrollment_ids = fields.One2many('university.enrollment', 'professor_id', string='Enrollments')

    enrollment_count = fields.Integer(compute='_compute_counts', string='Enrollment Count')

    @api.depends('enrollment_ids')
    def _compute_counts(self) -> None:
        """Calculates associated enrollments mapped by professor."""
        counts = self._get_batch_counts('university.enrollment', 'professor_id')
        for record in self:
            record.enrollment_count = counts.get(record.id, 0)


# Student
class UniversityStudent(models.Model):
    """Main model for student academic management."""
    _name = 'university.student'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'batch.count.mixin', 'image.mixin']
    _description = 'University Student'

    name = fields.Char(string='Name', required=True, index=True)
    email = fields.Char(string='Email', required=True, index=True)
    
    university_id = fields.Many2one('university.university', string='University', required=True, index=True)
    tutor_id = fields.Many2one(
        'university.professor',
        string='Tutor',
        ondelete='set null',
        domain="[('university_id', '=', university_id)]",
    )

    
    enrollment_ids = fields.One2many('university.enrollment', 'student_id', string='Enrollments')
    grade_ids = fields.One2many('university.grade', 'student_id', string='Grades')
    user_id = fields.Many2one('res.users', string='User', copy=False, index=True, ondelete='set null', readonly=True, help="Linked portal user.")

    street = fields.Char()
    city = fields.Char()
    state_id = fields.Many2one('res.country.state', domain="[('country_id', '=', country_id)]")
    zip_code = fields.Char()
    country_id = fields.Many2one('res.country')
    
    report_pending = fields.Boolean(string="Report Pending", default=False, index=True)

    enrollment_count = fields.Integer(compute='_compute_counts')
    grade_count = fields.Integer(compute='_compute_counts')

    _sql_constraints = [
        # Database-level uniqueness: faster, atomic, race-condition-proof vs. Python constraint alone
        ('unique_email', 'UNIQUE(email)', 'A student with this email already exists.'),
    ]

    @api.constrains('email')
    def _check_email_unique_login(self) -> None:
        """
        Validates that the student's email is not already used as a login
        by another res.users not linked to this student.
        Student uniqueness is enforced at the DB level via UNIQUE(email).

        Raises:
            ValidationError: If the email conflicts with an existing user login.
        """
        emails = {record.email for record in self if record.email}
        if not emails:
            return

        # sudo(): cross-model check requires elevated access to res.users
        user_login_map = {
            u.login: u.id
            for u in self.env['res.users'].sudo().search([('login', 'in', list(emails))])
        }
        if user_login_map:
            for record in self:
                if record.email in user_login_map:
                    linked_user_id = record.user_id.id if record.user_id else False
                    if user_login_map[record.email] != linked_user_id:
                        raise ValidationError(_(
                            "The email '%(email)s' is already registered as a user login.",
                            email=record.email,
                        ))


    @api.constrains('tutor_id', 'university_id')
    def _check_tutor_university(self) -> None:
        """
        Validates that the tutor belongs to the same university as the student.

        Raises:
            ValidationError: If the tutor belongs to a different university.
        """
        for record in self:
            if (
                record.tutor_id
                and record.tutor_id.university_id != record.university_id
            ):
                raise ValidationError(_("The tutor must belong to the same university as the student."))

    @api.model_create_multi
    def create(self, vals_list):
        """
        Intersects student creation to auto-provision and link portal users based on email.

        Args:
            vals_list (list): Dictionaries of student fields.

        Returns:
            Recordset: Newly created university.student records.
        """
        portal_group = self.env.ref('base.group_portal', raise_if_not_found=False)
        if not portal_group:
            raise UserError(_("Critical Error: 'base.group_portal' is missing. The system cannot provision portal users."))
            
        portal_group_id = portal_group.id

        emails = [vals.get('email') for vals in vals_list if vals.get('email') and not vals.get('user_id')]
        
        if emails:
            unique_emails = set(emails)
            # sudo(): provisioning portal users requires elevated access beyond student creator's rights
            existing_users = self.env['res.users'].sudo().search([('login', 'in', list(unique_emails))])
            user_map = {u.login: u.id for u in existing_users}

            emails_to_create = unique_emails - set(user_map.keys())

            if emails_to_create:
                user_vals = [{
                    'name': email,
                    'login': email,
                    'email': email,
                    'password': 'odoo',
                    # group_ids: Many2many on res.users — set portal group as the only group (Odoo 19: groups_id → group_ids)
                    'group_ids': [(6, 0, [portal_group_id])],
                } for email in emails_to_create]

                # sudo(): creating res.users requires admin-level privileges
                new_users = self.env['res.users'].sudo().create(user_vals)
                user_map.update({u.login: u.id for u in new_users})
            
            for vals in vals_list:
                email = vals.get('email')
                if email and not vals.get('user_id') and email in user_map:
                    vals['user_id'] = user_map[email]

        return super().create(vals_list)

    def write(self, vals):
        """
        Synchronizes portal user credentials when the student's email changes.
        Both the email AND login fields of the linked res.users are updated so
        the student can still log in after an email address change.
        """
        res = super().write(vals)
        if 'email' in vals:
            users_to_update = self.filtered('user_id').mapped('user_id').sudo()
            if users_to_update:
                users_to_update.write({
                    'email': vals['email'],
                    'login': vals['email'],
                })
        return res
  
    @api.depends('enrollment_ids', 'grade_ids')
    def _compute_counts(self) -> None:
        """Batch computes enrollment and grade counts linking them to the student."""
        enroll_map = self._get_batch_counts('university.enrollment', 'student_id')
        grade_map = self._get_batch_counts('university.grade', 'student_id')

        for record in self:
            record.enrollment_count = enroll_map.get(record.id, 0)
            record.grade_count = grade_map.get(record.id, 0)

    def action_send_email(self) -> dict[str, Any]:
        """
        Pops the mail composer pre-filled with the academic report template.
        """
        self.ensure_one()
        template = self.env.ref('university.email_template_student_report', raise_if_not_found=False)

        return {
            'name': _('Send Report'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'target': 'new',
            'context': {
                'default_model': self._name,
                'default_res_ids': self.ids,
                'default_template_id': template.id if template else False,
                'default_composition_mode': 'comment',
                'force_email': True,
            },
        }

    def action_send_email_silent_js(self) -> str | bool:
        """
        Pushes the academic report directly via the template preventing frontend blockage.

        Returns:
            str | bool: Target email address on success, False if no email configured.
        """
        self.ensure_one()
        if not self.email:
            return False

        template = self.env.ref('university.email_template_student_report')
        template.send_mail(self.id, force_send=True)  # bypass mail queue for immediate delivery
        return self.email

    @api.model
    def _cron_process_pending_reports(self) -> None:
        """
        Processes pending academic report emails in batches of 50 to avoid SMTP timeouts.
        Only students whose email was queued successfully are marked as processed.
        Failed sends retain report_pending=True so the next cron run retries them.
        """
        students = self.search([('report_pending', '=', True)], limit=50)
        if not students:
            return

        template = self.env.ref('university.email_template_student_report')

        success_ids: set[int] = set()
        error_ids: set[int] = set()

        for student in students:
            try:
                # force_send=False: delegate to mail queue for reliability under load
                template.send_mail(student.id, force_send=False)
                success_ids.add(student.id)
            except Exception as e:
                error_msg = f"Error generating/sending automatic report: {e}"
                _logger.error(
                    "Failed to generate report for Student %s: %s",
                    student.id, error_msg, exc_info=True
                )
                error_ids.add(student.id)
                student.message_post(body=error_msg, message_type='comment')

        if success_ids:
            self.browse(list(success_ids)).write({'report_pending': False})



class ResUsers(models.Model):
    """Users extension ensuring strict constraint mapping against student profiles."""
    _inherit = 'res.users'

    def _sync_university_students(self):
        """
        Links unlinked students to newly created/updated users by matching on email.
        Uses defaultdict to handle multiple students sharing the same email gracefully.
        """
        emails = [e for u in self for e in (u.login, u.email) if e]
        if not emails:
            return

        # sudo(): cross-user student lookup — a user provisioner may not see all students
        students = self.env['university.student'].sudo().search([
            ('email', 'in', emails),
            ('user_id', '=', False)
        ])

        if not students:
            return

        # Group students by email to handle edge case of duplicate emails: {email: [student1, ...]}
        student_map = defaultdict(list)
        for s in students:
            student_map[s.email].append(s)

        for user in self:
            matches = student_map.get(user.email) or student_map.get(user.login)
            if matches:
                match = matches.pop(0)  # take the first match; remaining stay unlinked
                match.user_id = user.id

    @api.model_create_multi
    def create(self, vals_list):
        """Forces newly provisioned system users to capture ownership of any orphaned students."""
        users = super().create(vals_list)
        users._sync_university_students()
        return users

    def write(self, vals):
        """Hooks onto credentials modifications binding orphaned students if matches resurface."""
        res = super().write(vals)
        if 'login' in vals or 'email' in vals:
            portal_users = self.filtered(lambda u: u.has_group('base.group_portal'))
            if portal_users:
                portal_users._sync_university_students()
        return res