import logging
from typing import Any, Dict, List, Optional

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


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
