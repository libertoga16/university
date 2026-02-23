import logging
from typing import Any, Dict, List, Optional

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class University(models.Model):
    """
    Architectural entity representing a University.

    Acts as the top-level container for all academic entities (departments, professors,
    students). It provides aggregate statistics and navigation to related sub-entities.
    """
    _name = 'university.university'
    _inherit = ['image.mixin', 'batch.count.mixin', 'website.published.mixin', 'website.seo.metadata']
    _description = 'University'

    #CORE FIELDS
    name = fields.Char(
        string='Name',
        required=True,
        index=True,
        help="Official name of the university."
    )
    email = fields.Char(
        string='Email',
        help="University email address."
    )

    #ADDRESS FIELDS 
    street = fields.Char(
        string='Street',
        help="Street address."
    )
    city = fields.Char(
        string='City',
        index=True,
        help="City."
    )
    country_id = fields.Many2one(
        comodel_name='res.country',
        string='Country',
        help="Country."
    )
    state_id = fields.Many2one(
        comodel_name='res.country.state',
        string='State',
        domain="[('country_id', '=', country_id)]",
        help="State or province."
    )
    zip_code = fields.Char(
        string='Zip Code',
        help="Postal code."
    )

    # RELATIONAL FIELDS 
    professor_ids = fields.One2many(
        comodel_name='university.professor',
        inverse_name='university_id',
        string='Professors',
        help="Professors employed by this university."
    )
    student_ids = fields.One2many(
        comodel_name='university.student',
        inverse_name='university_id',
        string='Students',
        help="Students registered at this university."
    )
    enrollment_ids = fields.One2many(
        comodel_name='university.enrollment',
        inverse_name='university_id',
        string='Enrollments',
        help="All enrollments across all subjects."
    )
    department_ids = fields.One2many(
        comodel_name='university.department',
        inverse_name='university_id',
        string='Departments',
        help="Departments within the university."
    )

    # === COMPUTED FIELDS ===
    professor_count = fields.Integer(
        compute='_compute_counts',
        string='Professor Count',
        help="Total number of professors."
    )
    student_count = fields.Integer(
        compute='_compute_counts',
        string='Student Count',
        help="Total number of students."
    )
    enrollment_count = fields.Integer(
        compute='_compute_counts',
        string='Enrollment Count',
        help="Total number of enrollments."
    )
    department_count = fields.Integer(
        compute='_compute_counts',
        string='Department Count',
        help="Total number of departments."
    )

    @api.depends('professor_ids', 'student_ids', 'enrollment_ids', 'department_ids')
    def _compute_counts(self) -> None:
        """
        Compute the number of related records for the smart buttons.
        """
        prof_map = self._get_batch_counts('university.professor', 'university_id')
        student_map = self._get_batch_counts('university.student', 'university_id')
        enroll_map = self._get_batch_counts('university.enrollment', 'university_id')
        dept_map = self._get_batch_counts('university.department', 'university_id')

        for record in self:
            record.professor_count = prof_map.get(record.id, 0)
            record.student_count = student_map.get(record.id, 0)
            record.enrollment_count = enroll_map.get(record.id, 0)
            record.department_count = dept_map.get(record.id, 0)
