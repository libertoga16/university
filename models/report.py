import logging
from typing import Any, Dict, List, Optional

from odoo import models, fields, tools, api

_logger = logging.getLogger(__name__)


class UniversityReport(models.Model):
    """
    Architectural entity representing a University Report (SQL View).

    A read-only aggregated view of student performance, flattening the
    relational structure for efficient reporting and analysis.
    """
    _name = 'university.report'
    _description = 'University Report'
    _auto = False
    _rec_name = 'student_id'

    # === DIMENSIONS (GROUP BY) ===
    university_id = fields.Many2one(
        comodel_name='university.university',
        string='University',
        readonly=True,
        help="University dimension."
    )
    professor_id = fields.Many2one(
        comodel_name='university.professor',
        string='Professor',
        readonly=True,
        help="Professor dimension."
    )
    department_id = fields.Many2one(
        comodel_name='university.department',
        string='Department',
        readonly=True,
        help="Department dimension."
    )
    student_id = fields.Many2one(
        comodel_name='university.student',
        string='Student',
        readonly=True,
        help="Student dimension."
    )
    subject_id = fields.Many2one(
        comodel_name='university.subject',
        string='Subject',
        readonly=True,
        help="Subject dimension."
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        readonly=True,
        help="Company dimension."
    )

    # === MEASURES (AGGREGATES) ===
    score = fields.Float(
        string='Score',
        readonly=True,
        aggregator='avg',
        help="Average score."
    )

    def init(self) -> None:
        """
        Initialize the SQL view.
        """
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                    row_number() OVER () AS id,
                    u.company_id AS company_id,
                    u.id AS university_id,
                    p.id AS professor_id,
                    d.id AS department_id,
                    s.id AS student_id,
                    sub.id AS subject_id,
                    g.score AS score -- Eliminar el COALESCE
                FROM
                    university_enrollment e
                LEFT JOIN
                    university_grade g ON g.enrollment_id = e.id
                JOIN
                    university_student s ON e.student_id = s.id
                JOIN
                    university_university u ON s.university_id = u.id
                JOIN
                    university_subject sub ON e.subject_id = sub.id
                LEFT JOIN
                    university_professor p ON e.professor_id = p.id
                LEFT JOIN
                    university_department d ON p.department_id = d.id
            )
        """ % (self._table))
