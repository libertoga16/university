import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


# Subject
class Subject(models.Model):
    """
    Architectural entity representing an Academic Subject.

    A specific course of study offered by a department. It links professors
    who teach it and students who enroll in it.
    """
    _name = 'university.subject'
    _inherit = ['batch.count.mixin']
    _description = 'Subject'

    # CORE FIELDS
    name = fields.Char(
        string='Name',
        required=True,
        index=True,
        help="Name of the subject."
    )
    code = fields.Char(
        string='Code',
        required=True,
        index=True,
        help="Unique identifier code."
    )

    # RELATIONAL FIELDS 
    department_id = fields.Many2one(
        comodel_name='university.department',
        string='Department',
        required=True,
        index=True,
        help="Department offering this subject."
    )
    university_id = fields.Many2one(
        comodel_name='university.university',
        related='department_id.university_id',
        string='University',
        store=True,
        readonly=True,
        index=True,
        help="University offering this subject (computed from department)."
    )
    professor_ids = fields.Many2many(
        comodel_name='university.professor',
        string='Professors',
        help="Professors qualified to teach this subject."
    )
    enrollment_ids = fields.One2many(
        comodel_name='university.enrollment',
        inverse_name='subject_id',
        string='Enrollments',
        help="All enrollments for this subject."
    )

    # COMPUTED FIELDS 
    enrollment_count = fields.Integer(
        compute='_compute_counts',
        string='Enrollment Count',
        help="Total number of students enrolled."
    )

    @api.depends('enrollment_ids')
    def _compute_counts(self) -> None:
        """
        Compute the number of enrollments for the subject.
        """
        enrollment_map = self._get_batch_counts('university.enrollment', 'subject_id')
        for record in self:
            record.enrollment_count = enrollment_map.get(record.id, 0)


# Enrollment
class Enrollment(models.Model):
    """
    Architectural entity representing a Student Enrollment.

    Junction record linking a student to a specific subject, professor, and university
    for a given academic term. It serves as the parent record for grades.
    """
    _name = 'university.enrollment'
    _description = 'Enrollment'
    _rec_name = 'code'

    # CORE FIELDS
    code = fields.Char(
        string='Code',
        required=True,
        default=lambda self: 'New',
        copy=False,
        index=True,
        help="Unique enrollment identifier."
    )

    # RELATIONAL FIELDS
    student_id = fields.Many2one(
        comodel_name='university.student',
        string='Student',
        required=True,
        index=True,
        help="enrolled student."
    )
    university_id = fields.Many2one(
        comodel_name='university.university',
        string='University',
        required=True,
        index=True,
        help="University where enrollment is registered."
    )
    professor_id = fields.Many2one(
        comodel_name='university.professor',
        string='Professor',
        index=True,
        help="Professor teaching the subject."
    )
    subject_id = fields.Many2one(
        comodel_name='university.subject',
        string='Subject',
        required=True,
        index=True,
        help="Subject being taken."
    )

    grade_ids = fields.One2many(
        comodel_name='university.grade',
        inverse_name='enrollment_id',
        string='Grades',
        help="Grades associated with this enrollment."
    )

    def _compute_display_name(self) -> None:
        """
        Compute the display name for the enrollment.
        Format: [Code] - [Student Name]
        """
        for record in self:
            record.display_name = f"{record.code} - {record.student_id.name}"

    @api.model_create_multi
    def create(self, vals_list: List[Dict[str, Any]]) -> Any:
        """
        Create enrollment records with auto-generated sequence codes.

        Architectural Decision: Optimization of Sequence Generation.
        We use the 'ir.sequence' model properly to handle concurrent sequence generation.
        """
        for vals in vals_list:
            if vals.get('code', 'New') == 'New':
                # Use standard Odoo sequence properly
                vals['code'] = self.env['ir.sequence'].next_by_code('university.enrollment') or 'New'

        return super(Enrollment, self).create(vals_list)

# Grade
class Grade(models.Model):
    """
    Architectural entity representing a Grade.

    Stores the score achieved by a student for a specific enrollment.
    """
    _name = 'university.grade'
    _description = 'Grade'

    # === RELATIONAL FIELDS ===
    enrollment_id = fields.Many2one(
        comodel_name='university.enrollment',
        string='Enrollment',
        required=True,
        index=True,
        help="Enrollment record this grade belongs to."
    )
    student_id = fields.Many2one(
        comodel_name='university.student',
        related='enrollment_id.student_id',
        string='Student',
        store=True,
        index=True,
        help="Student receiving the grade."
    )

    # === CORE FIELDS ===
    score = fields.Float(
        string='Score',
        index=True,
        help="Academic score."
    )
    date = fields.Date(
        string='Date',
        default=fields.Date.context_today,
        help="Date the grade was recorded."
    )

    def _compute_display_name(self) -> None:
        """
        Compute the display name for the grade.
        Format: [Student Name] - [Score]
        """
        for record in self:
            record.display_name = f"{record.student_id.name} - {record.score}"
