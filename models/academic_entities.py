import logging
from typing import Any, Dict, List, Optional
import base64

from odoo import models, fields, api

_logger = logging.getLogger(__name__)



# Department

class Department(models.Model):
    """
    Architectural entity representing a University Department.

    Organizes academic activities and personnel (professors) within a specific
    discipline or administrative unit.
    """
    _name = 'university.department'
    _description = 'Department'

    # CORE FIELDS 
    name = fields.Char(
        string='Name',
        required=True,
        index=True,
        help="Name of the department."
    )

    # RELATIONAL FIELDS
    university_id = fields.Many2one(
        comodel_name='university.university',
        string='University',
        required=True,
        index=True,
        help="University this department belongs to."
    )
    manager_id = fields.Many2one(
        comodel_name='university.professor',
        string='Manager',
        index=True,
        help="Professor managing this department."
    )
    professor_ids = fields.One2many(
        comodel_name='university.professor',
        inverse_name='department_id',
        string='Professors',
        help="Professors affiliated with this department."
    )

    # COMPUTED FIELDS
    professor_count = fields.Integer(
        compute='_compute_counts',
        string='Professor Count',
        help="Number of professors in this department."
    )

    @api.depends('professor_ids')
    def _compute_counts(self) -> None:
        """
        Compute the number of professors in the department.
        """
        if not self.ids:
            for record in self:
                record.professor_count = 0
            return
            
        domain = [('department_id', 'in', self.ids)]
        groups = self.env['university.professor']._read_group(domain, ['department_id'], ['__count'])
        count_map = {department.id: count for department, count in groups}
        
        for record in self:
            record.professor_count = count_map.get(record.id, 0)



# Professor

class UniversityProfessor(models.Model):
    """
    Architectural entity representing a University Professor.

    Academic staff member responsible for teaching subjects and managing
    departments. Links recursively to enrollments and departments.
    """
    _name = 'university.professor'
    _inherit = ['image.mixin']
    _description = 'University Professor'

    #  CORE FIELDS 
    name = fields.Char(
        string='Name',
        required=True,
        index=True,
        help="Full name of the professor."
    )
    email = fields.Char(
        string='Email',
        index=True,
        help="Professor's email address."
    )

    # RELATIONAL FIELDS 
    university_id = fields.Many2one(
        comodel_name='university.university',
        string='University',
        required=True,
        index=True,
        help="University affliation."
    )
    department_id = fields.Many2one(
        comodel_name='university.department',
        string='Department',
        required=True,
        index=True,
        help="Department this professor is a member of."
    )
    subject_ids = fields.Many2many(
        comodel_name='university.subject',
        string='Subjects',
        help="Subjects taught by this professor."
    )
    enrollment_ids = fields.One2many(
        comodel_name='university.enrollment',
        inverse_name='professor_id',
        string='Enrollments',
        help="Student enrollments in courses taught by this professor."
    )

    # COMPUTED FIELDS 
    enrollment_count = fields.Integer(
        compute='_compute_counts',
        string='Enrollment Count',
        help="Total number of student enrollments managed."
    )

    @api.depends('enrollment_ids')
    def _compute_counts(self) -> None:
        """
        Compute the number of enrollments associated with the professor.
        """
        if not self.ids:
            for record in self:
                record.enrollment_count = 0
            return

        domain = [('professor_id', 'in', self.ids)]
        groups = self.env['university.enrollment']._read_group(domain, ['professor_id'], ['__count'])
        count_map = {professor.id: count for professor, count in groups}

        for record in self:
            record.enrollment_count = count_map.get(record.id, 0)



# Student


class UniversityStudent(models.Model):
    _name = 'university.student'
    _inherit = ['mail.thread', 'mail.activity.mixin'] 
    _description = 'University Student'

    # CORE FIELDS 
    name = fields.Char(string='Name', required=True)
    email = fields.Char(string='Email')
    
    # RELATIONAL FIELDS
    university_id = fields.Many2one('university.university', string='University')
    tutor_id = fields.Many2one('university.professor', string='Tutor')
    
    enrollment_ids = fields.One2many('university.enrollment', 'student_id', string='Enrollments')
    grade_ids = fields.One2many('university.grade', 'student_id', string='Grades')

    user_id = fields.Many2one('res.users', string='User', readonly=True, help="Linked portal user.")

    # ADDRESS FIELDS
    street = fields.Char()
    city = fields.Char()
    state_id = fields.Many2one('res.country.state')
    zip_code = fields.Char()
    country_id = fields.Many2one('res.country')
    
    # IMAGE FIELDS
    image_1920 = fields.Image(string="Image")
    image_128 = fields.Image(related='image_1920', max_width=128, store=True, string="Thumbnail")

    # BACKGROUND PROCESSING FIELDS
    report_pending = fields.Boolean(string="Report Pending", default=False, help="Flag to indicate a report generation is pending for cron job.")

    # COMPUTED FIELDS
    enrollment_count = fields.Integer(compute='_compute_counts')
    grade_count = fields.Integer(compute='_compute_counts')

    # ORM OVERRIDES 
    @api.model_create_multi
    def create(self, vals_list):
        students = super().create(vals_list)
        users_to_create = []
        
        # 1. Preparar datos en memoria
        for student in students.filtered(lambda s: s.email and not s.user_id):
            users_to_create.append({
                'name': student.name,
                'login': student.email,
                'email': student.email,
                'group_ids': [(6, 0, [self.env.ref('base.group_portal').id])],
                'password': 'odoo' 
            })
        
        # 2. Inserción masiva con sudo()
        if users_to_create:
            new_users = self.env['res.users'].sudo().create(users_to_create)
            # 3. Mapeo eficiente
            for student, user in zip(students.filtered(lambda s: s.email and not s.user_id), new_users):
                student.user_id = user.id
                
        return students

    # BUSINESS LOGIC 
    
  
    @api.depends('enrollment_ids', 'grade_ids')
    def _compute_counts(self) -> None:
        """
        Compute counts for smart buttons using optimized batch queries.
        """
       
        if not self.ids:
            for record in self:
                record.enrollment_count = 0
                record.grade_count = 0
            return

        Enrollment = self.env['university.enrollment']
        Grade = self.env['university.grade']

        enroll_groups = Enrollment._read_group([('student_id', 'in', self.ids)], ['student_id'], ['__count'])
        enroll_map = {student.id: count for student, count in enroll_groups}

        grade_groups = Grade._read_group([('student_id', 'in', self.ids)], ['student_id'], ['__count'])
        grade_map = {student.id: count for student, count in grade_groups}

        for record in self:
            record.enrollment_count = enroll_map.get(record.id, 0)
            record.grade_count = grade_map.get(record.id, 0)

    def action_send_email(self) -> Dict[str, Any]:
        """
        Marks student as pending report generation for async processing.
        """
        self.write({'report_pending': True})
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Report Queued',
                'message': 'The academic report is being generated and will be sent shortly.',
                'type': 'success',
                'sticky': False,
            }
        }

    def action_send_email_silent_js(self) -> str | bool:
        """
        Genera el PDF y envía el correo en segundo plano sin intervención del usuario.
        Devuelve el email de destino para la notificación de JS.
        
        Returns:
            str | bool: El email de destino si es exitoso, False si no hay email vinculado.
        """
        self.ensure_one()
        
        if not self.email:
            return False

        template = self.env.ref('university.email_template_student_report')
        report_action = self.env.ref('university.action_report_student')
        
        pdf_content, _ = self.env['ir.actions.report']._render_qweb_pdf(report_action, self.ids)
        
        attachment = self.env['ir.attachment'].create({
            'name': f"Informe_{self.name.replace(' ', '_')}.pdf",
            'type': 'binary',
            'datas': base64.b64encode(pdf_content),
            'res_model': 'university.student',
            'res_id': self.id,
            'mimetype': 'application/pdf',
        })
        
        template.send_mail(
            self.id, 
            force_send=True, 
            email_values={'attachment_ids': [(4, attachment.id)]}
        )
        
        return self.email
        
    @api.model
    def _cron_process_pending_reports(self) -> None:
        """
        Cron job to process pending reports synchronously in background.
        """
        students = self.search([('report_pending', '=', True)])
        if not students:
            return
            
        template = self.env.ref('university.email_template_student_report')
        report_action = self.env.ref('university.action_report_student')
        
        for student in students:
            try:
                # Generate PDF
                pdf_content, _ = self.env['ir.actions.report']._render_qweb_pdf(report_action, student.ids)
                
                attachment = self.env['ir.attachment'].create({
                    'name': f"Informe_{student.name.replace(' ', '_')}.pdf",
                    'type': 'binary',
                    'datas': base64.b64encode(pdf_content),
                    'res_model': 'university.student',
                    'res_id': student.id,
                    'mimetype': 'application/pdf',
                })
                
                # Send Mail
                template.send_mail(
                    student.id, 
                    force_send=True,
                    email_values={'attachment_ids': [(4, attachment.id)]}
                )
                
                student.report_pending = False
                self.env.cr.commit() # Intermittent commit for large batches
            except Exception as e:
                _logger.error("Failed to generate report for Student %s: %s", student.id, e)

    def get_subject_summary(self):
        """Devuelve una lista de diccionarios con el resumen por asignatura"""
        self.ensure_one()
        summary = []
        # Prefetch de notas para evitar N+1 queries
        enrollments = self.enrollment_ids.with_context(prefetch_fields=False)
        enrollments.mapped('grade_ids') 
        
        for enrollment in enrollments:
            grades = enrollment.grade_ids
            # Evita sum() en python si puedes hacerlo por BD, o al menos no lo hagas por registro.
            avg_score = sum(grades.mapped('score')) / len(grades) if grades else 0.0
            
            summary.append({
                'subject': enrollment.subject_id.name,
                'professor': enrollment.professor_id.name or 'N/A',
                'average': avg_score
            })
        return summary


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model_create_multi
    def create(self, vals_list):
        """
        Al crear un nuevo usuario (portal o interno), buscar si hay algún estudiante
        con el mismo email y vincularlo automáticamente para que recupere sus notas pasadas.
        """
        users = super().create(vals_list)
        for user in users:
            emails_to_check = [e for e in [user.login, user.email] if e]
            if emails_to_check:
                students = self.env['university.student'].sudo().search([
                    ('email', 'in', emails_to_check),
                    ('user_id', '=', False)
                ])
                if students:
                    students.write({'user_id': user.id})
        return users

    def write(self, vals):
        """
        Si se actualiza el email/login de un usuario existente, intentar vincular
        estudiantes huérfanos que coincidan.
        """
        res = super().write(vals)
        if 'login' in vals or 'email' in vals:
            for user in self:
                emails_to_check = [e for e in [user.login, user.email] if e]
                if emails_to_check:
                    students = self.env['university.student'].sudo().search([
                        ('email', 'in', emails_to_check),
                        ('user_id', '=', False)
                    ])
                    if students:
                        students.write({'user_id': user.id})
        return res