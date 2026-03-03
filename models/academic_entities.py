import logging
from typing import Any, Dict

from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

# Department
class Department(models.Model):
    """Management of university departments."""
    _name = 'university.department'
    _inherit = ['batch.count.mixin']
    _description = 'Department'

    name = fields.Char(string='Name', required=True, index=True, help="Name of the department.")
    university_id = fields.Many2one('university.university', string='University', required=True, index=True, check_company=True)
    manager_id = fields.Many2one('university.professor', string='Manager', index=True, check_company=True)
    professor_ids = fields.One2many('university.professor', 'department_id', string='Professors')
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)

    professor_count = fields.Integer(compute='_compute_counts', string='Professor Count')

    @api.depends('professor_ids')
    def _compute_counts(self) -> None:
        """Computes the total number of professors in the department."""
        counts = self._get_batch_counts('university.professor', 'department_id')
        for record in self:
            record.professor_count = counts.get(record.id, 0)


# Professor
class UniversityProfessor(models.Model):
    """Management of university professors."""
    _name = 'university.professor'
    _inherit = ['image.mixin', 'batch.count.mixin', 'website.published.mixin', 'website.seo.metadata']
    _description = 'University Professor'

    name = fields.Char(string='Name', required=True, index=True)
    email = fields.Char(string='Email', index=True)
    
    university_id = fields.Many2one('university.university', string='University', required=True, index=True, check_company=True)
    department_id = fields.Many2one('university.department', string='Department', required=True, index=True, check_company=True)
    subject_ids = fields.Many2many('university.subject', string='Subjects')
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    enrollment_ids = fields.One2many('university.enrollment', 'professor_id', string='Enrollments')

    enrollment_count = fields.Integer(compute='_compute_counts', string='Enrollment Count')

    @api.depends('enrollment_ids')
    def _compute_counts(self) -> None:
        """Computes the number of enrollments associated with the professor."""
        counts = self._get_batch_counts('university.enrollment', 'professor_id')
        for record in self:
            record.enrollment_count = counts.get(record.id, 0)


# Student
class UniversityStudent(models.Model):
    """Main model for student academic management."""
    _name = 'university.student'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'batch.count.mixin'] 
    _description = 'University Student'

    name = fields.Char(string='Name', required=True, index=True)
    email = fields.Char(string='Email', required=True, index=True)
    
    university_id = fields.Many2one('university.university', string='University', check_company=True)
    tutor_id = fields.Many2one('university.professor', string='Tutor', check_company=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    
    enrollment_ids = fields.One2many('university.enrollment', 'student_id', string='Enrollments')
    grade_ids = fields.One2many('university.grade', 'student_id', string='Grades')
    user_id = fields.Many2one('res.users', string='User',copy=False,ondelete='set null', readonly=True, help="Linked portal user.")

    street = fields.Char()
    city = fields.Char()
    state_id = fields.Many2one('res.country.state')
    zip_code = fields.Char()
    country_id = fields.Many2one('res.country')
    
    image_1920 = fields.Image(string="Image")
    image_128 = fields.Image(related='image_1920', max_width=128, store=True, string="Thumbnail")

    report_pending = fields.Boolean(string="Report Pending", default=False, index=True)

    enrollment_count = fields.Integer(compute='_compute_counts')
    grade_count = fields.Integer(compute='_compute_counts')

    @api.model_create_multi
    def create(self, vals_list):
        """
        Overrides creation to automatically link or create portal users.

        Args:
            vals_list (list): Creation dictionaries.

        Returns:
            Recordset: Created students.

        Raises:
            UserError: If 'base.group_portal' group is missing.
        """
        portal_group = self.env.ref('base.group_portal', raise_if_not_found=False)
        if not portal_group:
            raise UserError(_("Critical Error: 'base.group_portal' is missing. The system cannot provision portal users."))
            
        portal_group_id = portal_group.id

        emails = [vals.get('email') for vals in vals_list if vals.get('email') and not vals.get('user_id')]
        
        if emails:
            unique_emails = set(emails)
            existing_users = self.env['res.users'].sudo().search([('login', 'in', list(unique_emails))])
            user_map = {u.login: u.id for u in existing_users}
            
            emails_to_create = unique_emails - set(user_map.keys())
            
            if emails_to_create:
                email_name_map = {
                    v.get('email'): v.get('name', v.get('email').split('@')[0]) 
                    for v in vals_list if v.get('email')
                }
                
                # Requirement: Generated user must be "Portal" type
                # This is achieved by injecting portal_group_id
                user_vals = [{
                    'name': email_name_map.get(email),
                    'login': email,
                    'email': email,
                    'group_ids': [(6, 0, [portal_group_id])],
                } for email in emails_to_create]
                
                new_users = self.env['res.users'].sudo().create(user_vals)
                user_map.update({u.login: u.id for u in new_users})
            
            # Requirement: Link to student automatically
            for vals in vals_list:
                email = vals.get('email')
                if email and not vals.get('user_id') and email in user_map:
                    vals['user_id'] = user_map[email]

        return super().create(vals_list)

    def write(self, vals):
        """
        Synchronizes email changes with the associated portal user.
        """
        res = super().write(vals)
        if 'email' in vals:
            for student in self.filtered('user_id'):
                student.user_id.sudo().write({
                    'login': vals['email'],
                    'email': vals['email']
                })
        return res
  
    @api.depends('enrollment_ids', 'grade_ids')
    def _compute_counts(self) -> None:
        """Batch computes enrollment and grade counts."""
        enroll_map = self._get_batch_counts('university.enrollment', 'student_id')
        grade_map = self._get_batch_counts('university.grade', 'student_id')

        for record in self:
            record.enrollment_count = enroll_map.get(record.id, 0)
            record.grade_count = grade_map.get(record.id, 0)

    def action_send_email(self) -> Dict[str, Any]:
        """Opens the composer. The report is attached automatically via XML."""
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
                # ZERO manual attachments here. The template does the work.
                'force_email': True,
            },
        }

    def action_send_email_silent_js(self) -> str | bool:
        """Sends silently. Odoo generates the PDF automatically."""
        self.ensure_one()
        if not self.email:
            return False

        template = self.env.ref('university.email_template_student_report')
        
        # A single real line of logic.
        template.send_mail(self.id, force_send=True)
        return self.email
        
    @api.model
    def _cron_process_pending_reports(self) -> None:
        """
        Processes asynchronous sending of academic reports via cron.
        
        Limits execution to prevent server timeouts.
        """
        students = self.search([('report_pending', '=', True)], limit=50)
        if not students:
            return

        template = self.env.ref('university.email_template_student_report')

        for student in students:
            try:
                # Cero adjuntos manuales. El template manda.
                template.send_mail(
                    student.id,
                    force_send=False  # Avoid SMTP timeout
                )
                student.report_pending = False
            except Exception as e:
                error_msg = f"Error generating/sending automatic report: {str(e)}"
                _logger.error(
                    "Failed to generate report for Student %s: %s",
                    student.id, error_msg, exc_info=True
                )
                student.message_post(body=error_msg, message_type='comment')



class ResUsers(models.Model):
    """Users extension for automatic assignment to students."""
    _inherit = 'res.users'

    def _sync_university_students(self):
        """Finds and links orphaned students with the current users based on email/login."""
        emails = [e for u in self for e in (u.login, u.email) if e]
        if not emails:
            return

        students = self.env['university.student'].sudo().search([
            ('email', 'in', emails),
            ('user_id', '=', False)
        ])
        
        if not students:
            return

        from collections import defaultdict
        student_map = defaultdict(list)
        for s in students:
            student_map[s.email].append(s)
        
        for user in self:
            matches = student_map.get(user.email) or student_map.get(user.login)
            if matches:
                match = matches.pop(0) 
                match.user_id = user.id

    @api.model_create_multi
    def create(self, vals_list):
        """Links new users to matching student if exists."""
        users = super().create(vals_list)
        users._sync_university_students()
        return users

    def write(self, vals):
        """Relinks user to student if login or email is updated."""
        res = super().write(vals)
        if 'login' in vals or 'email' in vals:
            self._sync_university_students()
        return res