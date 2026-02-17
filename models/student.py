import logging
from typing import Any, Dict, List, Optional

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class UniversityStudent(models.Model):
    """
    Architectural entity representing a student within the university system.
    
    This model serves as the central node for student academic lifecycle management,
    aggregating enrollments, grades, and personal data. It integrates with the
    mail system for communication and report dissemination.
    """
    _name = 'university.student'
    _inherit = ['image.mixin', 'mail.thread', 'mail.activity.mixin', 'batch.count.mixin']
    _description = 'University Student'

    # === CORE FIELDS ===
    name = fields.Char(
        string='Name',
        required=True,
        index=True,
        help="Full name of the student."
    )
    email = fields.Char(
        string='Email',
        index=True,
        help="Primary email address for communication and reporting."
    )

    # === RELATIONAL FIELDS ===
    university_id = fields.Many2one(
        comodel_name='university.university',
        string='University',
        required=True,
        index=True,
        help="The university the student is currently registered with."
    )
    tutor_id = fields.Many2one(
        comodel_name='university.professor',
        string='Tutor',
        index=True,
        help="Assigned academic tutor for the student."
    )
    enrollment_ids = fields.One2many(
        comodel_name='university.enrollment',
        inverse_name='student_id',
        string='Enrollments',
        help="List of course enrollments for this student."
    )
    grade_ids = fields.One2many(
        comodel_name='university.grade',
        inverse_name='student_id',
        string='Grades',
        help="List of academic grades received by this student."
    )

    # === ADDRESS FIELDS ===
    street = fields.Char(
        string='Street',
        help="Street address."
    )
    city = fields.Char(
        string='City',
        index=True,
        help="City."
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
    country_id = fields.Many2one(
        comodel_name='res.country',
        string='Country',
        help="Country."
    )

    # === COMPUTED FIELDS ===
    enrollment_count = fields.Integer(
        compute='_compute_counts',
        string='Enrollment Count',
        help="Total number of active enrollments."
    )
    grade_count = fields.Integer(
        compute='_compute_counts',
        string='Grade Count',
        help="Total number of recorded grades."
    )

    @api.depends('enrollment_ids', 'grade_ids')
    def _compute_counts(self) -> None:
        """
        Compute the number of enrollments and grades for the student.
        """
        enrollment_map = self._get_batch_counts('university.enrollment', 'student_id')
        grade_map = self._get_batch_counts('university.grade', 'student_id')

        for record in self:
            record.enrollment_count = enrollment_map.get(record.id, 0)
            record.grade_count = grade_map.get(record.id, 0)

    def action_send_email(self) -> Dict[str, Any]:
        """
        Opens a wizard to compose an email, with the template pre-loaded.

        Returns:
            Dict[str, Any]: The action dictionary to open the mail composition wizard.
        """
        self.ensure_one()
        template = self.env.ref('university.email_template_student_report', raise_if_not_found=False)
        
        template_id: int = template.id if template else False
        
        ctx: Dict[str, Any] = {
            'default_model': 'university.student',
            'default_res_ids': self.ids,
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'force_email': True,
        }
        
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }
