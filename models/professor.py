import logging
from typing import Any, Dict, List, Optional

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class UniversityProfessor(models.Model):
    """
    Architectural entity representing a University Professor.
    
    Academic staff member responsible for teaching subjects and managing
    departments. Links recursively to enrollments and departments.
    """
    _name = 'university.professor'
    _inherit = ['image.mixin', 'batch.count.mixin']
    _description = 'University Professor'

    # === CORE FIELDS ===
    name = fields.Char(
        string='Name',
        required=True,
        index=True,
        help="Full name of the professor."
    )

    # === RELATIONAL FIELDS ===
    university_id = fields.Many2one(
        comodel_name='university.university',
        string='University',
        required=True,
        index=True,
        help="University affliation."
    )
    department_ids = fields.Many2many(
        comodel_name='university.department',
        relation='university_prof_dept_rel',
        column1='prof_id',
        column2='dept_id',
        string='Departments',
        help="Departments this professor is a member of."
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

    # === COMPUTED FIELDS ===
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
