import logging
from typing import Any, Dict, List, Optional

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class EnrollmentWizard(models.TransientModel):
    """
    Wizard for bulk enrollment of students.

    Allows selecting a university, subject, and professor, and then
    enrolling multiple students at once.
    """
    _name = 'university.enrollment.wizard'
    _description = 'Enrollment Wizard'

    def _default_university(self) -> Optional[models.Model]:
        return self.env['university.university'].search([], limit=1)

    # === SELECTION FIELDS ===
    university_id = fields.Many2one(
        comodel_name='university.university',
        string='University',
        required=True,
        default=_default_university,
        help="University context for enrollment."
    )
    subject_id = fields.Many2one(
        comodel_name='university.subject',
        string='Subject',
        required=True,
        domain="[('university_id', '=', university_id)]",
        help="Subject to enroll students in."
    )
    professor_id = fields.Many2one(
        comodel_name='university.professor',
        string='Professor',
        domain="[('university_id', '=', university_id)]",
        help="Professor teaching the subject."
    )
    student_ids = fields.Many2many(
        comodel_name='university.student',
        string='Students',
        required=True,
        domain="[('university_id', '=', university_id)]",
        help="Students to enroll."
    )

    @api.onchange('university_id')
    def _onchange_university_id(self) -> None:
        """
        Reset fields when university changes to prevent inconsistent data.
        """
        self.subject_id = False
        self.professor_id = False
        self.student_ids = False

    def action_enroll(self) -> Dict[str, Any]:
        """
        Create enrollments for selected students.

        Performs a bulk create operation for performance optimization.
        """
        self.ensure_one()

        if not self.student_ids:
            return {'type': 'ir.actions.act_window_close'}

        # Architectural Decision: Bulk Creation.
        # Construct a list of dictionaries to perform a single DB insert for all enrollments.
        vals_list: List[Dict[str, Any]] = [
            {
                'student_id': student.id,
                'university_id': self.university_id.id,
                'subject_id': self.subject_id.id,
                'professor_id': self.professor_id.id if self.professor_id else False,
            }
            for student in self.student_ids
        ]

        # Use batch create
        enrollments = self.env['university.enrollment'].create(vals_list)

        _logger.info(f"Batch created {len(enrollments)} enrollments via wizard.")

        return {
            'name': _('Created Enrollments'),
            'type': 'ir.actions.act_window',
            'view_mode': 'list,form',
            'res_model': 'university.enrollment',
            'domain': [('id', 'in', enrollments.ids)],
            'target': 'current',
        }
