import logging
from typing import Any, Dict, List, Optional

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class Subject(models.Model):
    """
    Architectural entity representing an Academic Subject.
    
    A specific course of study offered by a department. It links professors
    who teach it and students who enroll in it.
    """
    _name = 'university.subject'
    _inherit = ['batch.count.mixin']
    _description = 'Subject'

    # === CORE FIELDS ===
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

    # === RELATIONAL FIELDS ===
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

    # === COMPUTED FIELDS ===
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
