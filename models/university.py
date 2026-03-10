import logging
from typing import Any, Dict, List, Optional

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class University(models.Model):
    """Main entity grouping departments, professors, and students."""
    _name = 'university.university'
    _inherit = ['image.mixin', 'batch.count.mixin', 'website.published.mixin', 'website.seo.metadata']
    _description = 'University'

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


    # ADDRESS FIELDS
    street = fields.Char(
        string='Street',
        help="Street address."
    )
    city = fields.Char(
        string='City',
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
    director_id = fields.Many2one(
        comodel_name='university.professor',
        string='Director',
        domain="['|', ('university_id', '=', id), ('university_id', '=', False)]",
        help="Director de la universidad."
    )
    professor_ids = fields.One2many(
        comodel_name='university.professor',
        inverse_name='university_id',
        string='Professors'
    )
    student_ids = fields.One2many(
        comodel_name='university.student',
        inverse_name='university_id',
        string='Students'
    )
    enrollment_ids = fields.One2many(
        comodel_name='university.enrollment',
        inverse_name='university_id',
        string='Enrollments'
    )
    department_ids = fields.One2many(
        comodel_name='university.department',
        inverse_name='university_id',
        string='Departments'
    )

    # COMPUTED FIELDS
    professor_count = fields.Integer(
        compute='_compute_counts',
        string='Professor Count'
    )
    student_count = fields.Integer(
        compute='_compute_counts',
        string='Student Count'
    )
    enrollment_count = fields.Integer(
        compute='_compute_counts',
        string='Enrollment Count'
    )
    department_count = fields.Integer(
        compute='_compute_counts',
        string='Department Count'
    )

    @api.depends('professor_ids', 'student_ids', 'enrollment_ids', 'department_ids')
    def _compute_counts(self) -> None:
        """Computes the number of related records for smart buttons without N+1 queries."""
        prof_map = self._get_batch_counts('university.professor', 'university_id')
        student_map = self._get_batch_counts('university.student', 'university_id')
        enroll_map = self._get_batch_counts('university.enrollment', 'university_id')
        dept_map = self._get_batch_counts('university.department', 'university_id')

        for record in self:
            record.professor_count = prof_map.get(record.id, 0)
            record.student_count = student_map.get(record.id, 0)
            record.enrollment_count = enroll_map.get(record.id, 0)
            record.department_count = dept_map.get(record.id, 0)

    @api.constrains('director_id')
    def _check_director_university(self) -> None:
        """
        Validates that the assigned director belongs to the university.
        Raises ValidationError if the constraint is violated.
        """
        for record in self:
            if (
                record.director_id
                and record.director_id.university_id
                and record.director_id.university_id != record
            ):
                raise ValidationError(_("The director must belong to the same university."))