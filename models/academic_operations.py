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

    department_id = fields.Many2one('university.department', string='Department', required=True, index=True)
    university_id = fields.Many2one(
        'university.university', related='department_id.university_id', 
        store=True, readonly=True, index=True
    )
    professor_ids = fields.Many2many('university.professor', string='Professors')
    enrollment_ids = fields.One2many('university.enrollment', 'subject_id', string='Enrollments')

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

    student_id = fields.Many2one('university.student', string='Student', required=True, index=True)
    university_id = fields.Many2one('university.university', string='University', required=True, index=True)
    professor_id = fields.Many2one('university.professor', string='Professor', index=True)
    subject_id = fields.Many2one('university.subject', string='Subject', required=True, index=True)
    grade_ids = fields.One2many('university.grade', 'enrollment_id', string='Grades')

    @api.depends('code', 'student_id.name')
    def _compute_display_name(self) -> None:
        for record in self:
            record.display_name = f"{record.code or ''} - {record.student_id.name or ''}"

    @api.model_create_multi
    def create(self, vals_list: List[Dict[str, Any]]) -> Any:
        # Standard approach: Utilize ir.sequence explicitly for batch creation.
        # Calling private methods like `sequence._next()` is bad practice in Odoo 19.
        if not self.env.context.get('skip_sequence_generation'):
            for vals in vals_list:
                if vals.get('code', 'New') == 'New':
                    vals['code'] = self.env['ir.sequence'].next_by_code('university.enrollment') or 'New'
        return super().create(vals_list)


# Grade
class Grade(models.Model):
    _name = 'university.grade'
    _description = 'Grade'

    enrollment_id = fields.Many2one('university.enrollment', string='Enrollment', required=True, index=True)
    student_id = fields.Many2one(
        'university.student', related='enrollment_id.student_id', 
        store=True, index=True
    )

    score = fields.Float(string='Score', index=True)
    date = fields.Date(string='Date', default=fields.Date.context_today)

    @api.depends('student_id.name', 'score')
    def _compute_display_name(self) -> None:
        for record in self:
            record.display_name = f"{record.student_id.name or ''} - {record.score or 0.0}"
