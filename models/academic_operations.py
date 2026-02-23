import logging
from typing import Any, Dict, List

from odoo import models, fields, api

_logger = logging.getLogger(__name__)

# Subject
class Subject(models.Model):
    _name = 'university.subject'
    _inherit = ['batch.count.mixin']
    _description = 'Subject'

    name = fields.Char(string='Name', required=True, index=True)
    code = fields.Char(string='Code', required=True, index=True)

    department_id = fields.Many2one('university.department', string='Department', required=True, index=True, check_company=True)
    university_id = fields.Many2one(
        'university.university', related='department_id.university_id', 
        store=True, readonly=True, index=True, check_company=True
    )
    professor_ids = fields.Many2many('university.professor', string='Professors')
    enrollment_ids = fields.One2many('university.enrollment', 'subject_id', string='Enrollments')
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)

    enrollment_count = fields.Integer(compute='_compute_counts', string='Enrollment Count')

    @api.depends('enrollment_ids')
    def _compute_counts(self) -> None:
        counts = self._get_batch_counts('university.enrollment', 'subject_id')
        for record in self:
            record.enrollment_count = counts.get(record.id, 0)


# Enrollment
class Enrollment(models.Model):
    _name = 'university.enrollment'
    _description = 'Enrollment'
    _rec_name = 'code'

    code = fields.Char(string='Code', required=True, default='New', copy=False, index=True)

    student_id = fields.Many2one('university.student', string='Student', required=True, index=True, check_company=True)
    university_id = fields.Many2one('university.university', string='University', required=True, index=True, check_company=True)
    professor_id = fields.Many2one('university.professor', string='Professor', index=True, check_company=True)
    subject_id = fields.Many2one('university.subject', string='Subject', required=True, index=True, check_company=True)
    grade_ids = fields.One2many('university.grade', 'enrollment_id', string='Grades')
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)

    _sql_constraints = [
        ('unique_student_subject', 
         'UNIQUE(student_id, subject_id)', 
         'Integrity Error: A student cannot be enrolled more than once in the same subject.')
    ]

    @api.depends('code', 'student_id.name')
    def _compute_display_name(self) -> None:
        for record in self:
            record.display_name = f"{record.code or ''} - {record.student_id.name or ''}"

    @api.model_create_multi
    def create(self, vals_list: List[Dict[str, Any]]) -> Any:
        # 1. Extraer IDs únicos de asignaturas necesarias para las nuevas matrículas
        subject_ids = {
            vals['subject_id'] 
            for vals in vals_list 
            if vals.get('code', 'New') == 'New' and vals.get('subject_id')
        }
        
        if subject_ids:
            subjects = self.env['university.subject'].browse(list(subject_ids))
            seq_map = {}
            
            # 2. Buscar o crear todas las secuencias necesarias en lote
            for subject in subjects:
                seq_code = f"enrollment.subject.{subject.id}"
                seq = self.env['ir.sequence'].sudo().search([('code', '=', seq_code)], limit=1)
                
                if not seq:
                    prefix_str = (subject.name[:3].upper() if subject.name else 'UNK')
                    seq = self.env['ir.sequence'].sudo().create({
                        'name': f'Enrollment Sequence {subject.name}',
                        'code': seq_code,
                        'prefix': f"{prefix_str}/%(year)s/",
                        'padding': 4,
                        'use_date_range': True,
                        'company_id': False,
                    })
                seq_map[subject.id] = seq

            # 3. Asignar los códigos iterando solo en memoria RAM
            for vals in vals_list:
                if vals.get('code', 'New') == 'New' and vals.get('subject_id'):
                    vals['code'] = seq_map[vals['subject_id']].next_by_id()
                    
        return super().create(vals_list)


# Grade
class Grade(models.Model):
    _name = 'university.grade'
    _description = 'Grade'

    enrollment_id = fields.Many2one('university.enrollment', string='Enrollment', required=True, index=True, check_company=True)
    student_id = fields.Many2one(
        'university.student', related='enrollment_id.student_id', 
        store=True, index=True, check_company=True
    )

    score = fields.Float(string='Score', index=True)
    date = fields.Date(string='Date', default=fields.Date.context_today)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)

    @api.depends('student_id.name', 'score')
    def _compute_display_name(self) -> None:
        for record in self:
            record.display_name = f"{record.student_id.name or ''} - {record.score or 0.0}"
