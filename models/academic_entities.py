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
    _inherit = ['batch.count.mixin']
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
        prof_map = self._get_batch_counts('university.professor', 'department_id')
        for record in self:
            record.professor_count = prof_map.get(record.id, 0)



# Professor

class UniversityProfessor(models.Model):
    """
    Architectural entity representing a University Professor.

    Academic staff member responsible for teaching subjects and managing
    departments. Links recursively to enrollments and departments.
    """
    _name = 'university.professor'
    _inherit = ['image.mixin', 'batch.count.mixin']
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
        enrollment_map = self._get_batch_counts('university.enrollment', 'professor_id')
        for record in self:
            record.enrollment_count = enrollment_map.get(record.id, 0)



# Student


class UniversityStudent(models.Model):
    _name = 'university.student'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'batch.count.mixin'] 
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

    # COMPUTED FIELDS 
    enrollment_count = fields.Integer(compute='_compute_counts')
    grade_count = fields.Integer(compute='_compute_counts')

    # ORM OVERRIDES 
    @api.model_create_multi
    def create(self, vals_list):
        students = super(UniversityStudent, self).create(vals_list)
        
        # Auto-create Portal User for each new student
        for student in students:
            if student.email and not student.user_id:
                user = self.env['res.users'].search([('login', '=', student.email)], limit=1)
                if not user:
                    user = self.env['res.users'].create({
                        'name': student.name,
                        'login': student.email,
                        'email': student.email,
                        'group_ids': [(6, 0, [self.env.ref('base.group_portal').id])],
                        'password': 'odoo' 
                    })
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

        enroll_map = self._get_batch_counts('university.enrollment', 'student_id')
        grade_map = self._get_batch_counts('university.grade', 'student_id')

        for record in self:
            record.enrollment_count = enroll_map.get(record.id, 0)
            record.grade_count = grade_map.get(record.id, 0)

    def action_send_email(self) -> Dict[str, Any]:
        """
        Generates the PDF report and opens the email composer with it attached.
        """
        self.ensure_one()
        template = self.env.ref('university.email_template_student_report')
        
        ctx = {
            'default_model': 'university.student',
            'default_res_ids': self.ids,
            'default_use_template': bool(template),
            'default_template_id': template.id,
            'default_composition_mode': 'comment',
            'force_email': True,
        }

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
        
        ctx['default_attachment_ids'] = [(4, attachment.id)]
        
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }

    def get_subject_summary(self):
        """Devuelve una lista de diccionarios con el resumen por asignatura"""
        summary = []
        for enrollment in self.enrollment_ids:
            grades = enrollment.grade_ids
            avg_score = sum(grades.mapped('score')) / len(grades) if grades else 0.0
            
            summary.append({
                'subject': enrollment.subject_id.name,
                'professor': enrollment.professor_id.name or 'N/A',
                'average': avg_score
            })
        return summary