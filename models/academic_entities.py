import logging
import base64
from typing import Any, Dict

from odoo import models, fields, api

_logger = logging.getLogger(__name__)

# Department
class Department(models.Model):
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
        counts = self._get_batch_counts('university.professor', 'department_id')
        for record in self:
            record.professor_count = counts.get(record.id, 0)


# Professor
class UniversityProfessor(models.Model):
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
        counts = self._get_batch_counts('university.enrollment', 'professor_id')
        for record in self:
            record.enrollment_count = counts.get(record.id, 0)


# Student
class UniversityStudent(models.Model):
    _name = 'university.student'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'batch.count.mixin'] 
    _description = 'University Student'

    name = fields.Char(string='Name', required=True)
    email = fields.Char(string='Email')
    
    university_id = fields.Many2one('university.university', string='University', check_company=True)
    tutor_id = fields.Many2one('university.professor', string='Tutor', check_company=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    
    enrollment_ids = fields.One2many('university.enrollment', 'student_id', string='Enrollments')
    grade_ids = fields.One2many('university.grade', 'student_id', string='Grades')
    user_id = fields.Many2one('res.users', string='User', readonly=True, help="Linked portal user.")

    street = fields.Char()
    city = fields.Char()
    state_id = fields.Many2one('res.country.state')
    zip_code = fields.Char()
    country_id = fields.Many2one('res.country')
    
    image_1920 = fields.Image(string="Image")
    image_128 = fields.Image(related='image_1920', max_width=128, store=True, string="Thumbnail")

    report_pending = fields.Boolean(string="Report Pending", default=False)

    enrollment_count = fields.Integer(compute='_compute_counts')
    grade_count = fields.Integer(compute='_compute_counts')

    @api.model_create_multi
    def create(self, vals_list):
        students = super().create(vals_list)
        portal_group = self.env.ref('base.group_portal').id
        
        # 1. Identificar estudiantes que necesitan usuario
        students_to_link = students.filtered(lambda s: s.email and not s.user_id)
        
        if students_to_link:
            # 2. Preparar el lote de creación
            user_vals = [{
                'name': s.name,
                'login': s.email,
                'email': s.email,
                'groups_id': [(6, 0, [portal_group])],
            } for s in students_to_link]
            
            # 3. Inserción única masiva (1 sola query)
            users = self.env['res.users'].sudo().create(user_vals)
            
            # 4. Enlace en memoria seguro (evita errores de orden del zip)
            users_by_email = {u.email: u for u in users}
            for student in students_to_link:
                if student.email in users_by_email:
                    student.user_id = users_by_email[student.email].id
                    
        return students
  
    @api.depends('enrollment_ids', 'grade_ids')
    def _compute_counts(self) -> None:
        enroll_map = self._get_batch_counts('university.enrollment', 'student_id')
        grade_map = self._get_batch_counts('university.grade', 'student_id')

        for record in self:
            record.enrollment_count = enroll_map.get(record.id, 0)
            record.grade_count = grade_map.get(record.id, 0)

    def action_send_email(self) -> Dict[str, Any]:
        self.ensure_one()
        template = self.env.ref('university.email_template_student_report', raise_if_not_found=False)
        return {
            'name': 'Enviar Reporte',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': {
                'default_model': 'university.student',
                'default_res_ids': self.ids,
                'default_template_id': template.id if template else False,
                'default_composition_mode': 'comment',
                'force_email': True,
            },
        }

    def action_send_email_silent_js(self) -> str | bool:
        self.ensure_one()
        if not self.email:
            return False

        template = self.env.ref('university.email_template_student_report')
        report_action = self.env.ref('university.action_report_student')
        
        # LLAMADA CORRECTA A LA API DE ODOO 19
        pdf_content, _ = report_action._render_qweb_pdf(self.ids)
        
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
        # Limit added to prevent cron timeouts. Let it run naturally without forcing manual DB commits.
        students = self.search([('report_pending', '=', True)], limit=50)
        if not students:
            return
            
        template = self.env.ref('university.email_template_student_report')
        report_action = self.env.ref('university.action_report_student')
        
        for student in students:
            try:
                pdf_content, _ = report_action._render_qweb_pdf(student.ids)
                attachment = self.env['ir.attachment'].create({
                    'name': f"Informe_{student.name.replace(' ', '_')}.pdf",
                    'type': 'binary',
                    'datas': base64.b64encode(pdf_content),
                    'res_model': 'university.student',
                    'res_id': student.id,
                    'mimetype': 'application/pdf',
                })
                
                template.send_mail(
                    student.id, 
                    force_send=False, # NUNCA fuerces el envío dentro de un bucle cron (evita SMTP timeout)
                    email_values={'attachment_ids': [(4, attachment.id)]}
                )
                student.report_pending = False
            except Exception as e:
                _logger.error("Failed to generate report for Student %s: %s", student.id, e)

    def get_subject_summary(self):
        self.ensure_one()
        
        # Optimized via DB aggregation instead of Python loops
        groups = self.env['university.grade']._read_group(
            domain=[('student_id', '=', self.id)],
            groupby=['enrollment_id'],
            aggregates=['score:avg']
        )
        
        summary = []
        for enrollment, avg_score in groups:
            summary.append({
                'subject': enrollment.subject_id.name,
                'professor': enrollment.professor_id.name or 'N/A',
                'average': avg_score or 0.0
            })
        return summary

class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model_create_multi
    def create(self, vals_list):
        users = super().create(vals_list)
        
        emails = [e for u in users for e in (u.login, u.email) if e]
        if emails:
            students = self.env['university.student'].sudo().search([
                ('email', 'in', emails),
                ('user_id', '=', False)
            ])
            
            # Mapeo seguro agrupando en listas para no perder colisiones
            from collections import defaultdict
            student_map = defaultdict(list)
            for s in students:
                student_map[s.email].append(s)
            
            for user in users:
                matches = student_map.get(user.email) or student_map.get(user.login)
                if matches:
                    # Enlazar al primer estudiante huérfano encontrado
                    match = matches.pop(0) 
                    match.user_id = user.id
        return users

    def write(self, vals):
        res = super().write(vals)
        # Optimizar también la escritura
        if 'login' in vals or 'email' in vals:
            emails = [e for u in self for e in (u.login, u.email) if e]
            if emails:
                students = self.env['university.student'].sudo().search([
                    ('email', 'in', emails),
                    ('user_id', '=', False)
                ])
                student_map = {s.email: s for s in students}
                for user in self:
                    match = student_map.get(user.email) or student_map.get(user.login)
                    if match:
                        match.user_id = user.id
        return res