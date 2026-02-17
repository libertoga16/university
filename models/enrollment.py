import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class Enrollment(models.Model):
    """
    Architectural entity representing a Student Enrollment.
    
    Junction record linking a student to a specific subject, professor, and university
    for a given academic term. It serves as the parent record for grades.
    """
    _name = 'university.enrollment'
    _description = 'Enrollment'
    _rec_name = 'code'

    # === CORE FIELDS ===
    code = fields.Char(
        string='Code',
        required=True,
        default=lambda self: 'New',
        copy=False,
        index=True,
        help="Unique enrollment identifier."
    )

    # === RELATIONAL FIELDS ===
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

        Architectural Decision: Custom Sequence Logic.
        Generates a code in format prefix/year/sequence (e.g., MATH/2023/0001).
        Logic handles bulk creation.
        
        Args:
            vals_list: List of dictionaries containing field values.
            
        Returns:
            The created recordset.
        """
        for vals in vals_list:
            if vals.get('subject_id'):
                subject = self.env['university.subject'].browse(vals['subject_id'])
                if subject:
                    prefix = subject.name[:3].upper() if subject.name else 'UNK'
                    year = datetime.now().year
                    pattern = f"{prefix}/{year}/%"
                    
                    # Find last sequence for this subject and year
                    # Note: This is susceptible to race conditions in high concurrency
                    # but acceptable for this scale. Enterprise Odoo would use ir.sequence.
                    last_enrollment = self.search([('code', 'like', pattern)], order='code desc', limit=1)
                    
                    if last_enrollment:
                        try:
                            # Extract sequence number (last 4 digits)
                            last_seq = int(last_enrollment.code.split('/')[-1])
                            new_seq = last_seq + 1
                        except ValueError:
                            new_seq = 1
                    else:
                        new_seq = 1
                    
                    vals['code'] = f"{prefix}/{year}/{new_seq:04d}"
        
        return super(Enrollment, self).create(vals_list)
