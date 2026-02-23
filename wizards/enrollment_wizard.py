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
        Create enrollments for selected students, preventing duplicates.
        """
        self.ensure_one()
        if not self.student_ids:
            return {'type': 'ir.actions.act_window_close'}

        # Obtener IDs de alumnos que ya están inscritos en esta materia
        existing_enrollments = self.env['university.enrollment'].search([
            ('subject_id', '=', self.subject_id.id),
            ('student_id', 'in', self.student_ids.ids)
        ])
        enrolled_student_ids = existing_enrollments.mapped('student_id.id')

        # Filtrar solo los alumnos que NO están inscritos
        valid_students = self.student_ids.filtered(lambda s: s.id not in enrolled_student_ids)

        if not valid_students:
            # Opción: Lanzar ValidationError o simplemente retornar
            raise ValidationError(_("Todos los alumnos seleccionados ya están inscritos en esta asignatura."))

        vals_list = [{
            'student_id': student.id,
            'university_id': self.university_id.id,
            'subject_id': self.subject_id.id,
            'professor_id': self.professor_id.id if self.professor_id else False,
        } for student in valid_students]

        enrollments = self.env['university.enrollment'].create(vals_list)
        
        return {
            'name': _('Created Enrollments'),
            'type': 'ir.actions.act_window',
            'view_mode': 'list,form',
            'res_model': 'university.enrollment',
            'domain': [('id', 'in', enrollments.ids)],
            'target': 'current',
        }
