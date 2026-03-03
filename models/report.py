import logging
from typing import Any, Dict, List, Optional

from odoo import models, fields, tools, api

_logger = logging.getLogger(__name__)


class UniversityReport(models.Model):
    """Aggregated SQL view of student performance (Read-only)."""
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
        """Initializes the report's SQL view."""
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
                    g.score AS score -- Remove COALESCE
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


class StudentReportParser(models.AbstractModel):
    """Parser to inject computed data into the students report QWeb."""
    _name = 'report.university.report_student_template'
    _description = 'Student Report Parser'

    @api.model
    def _get_report_values(self, docids, data=None):
        """
        Generates aggregated data for the report.

        Args:
            docids (list): Student IDs.
            data (dict, optional): Additional data.

        Returns:
            dict: Values injected into QWeb.
        """
        docs = self.env['university.student'].browse(docids)
        
        # Get ALL averages for ALL students in 1 single SQL query
        groups = self.env['university.grade']._read_group(
            domain=[('student_id', 'in', docids)],
            groupby=['student_id', 'enrollment_id'],
            aggregates=['score:avg']
        )
        
        # Map in memory
        summary_by_student = {doc_id: [] for doc_id in docids}
        for student, enrollment, avg_score in groups:
            summary_by_student[student.id].append({
                'subject': enrollment.subject_id.name,
                'professor': enrollment.professor_id.name or 'N/A',
                'average': avg_score or 0.0
            })
            
        # Inject the pre-calculated dictionary into QWeb
        return {
            'docs': docs,
            'student_summaries': summary_by_student,
        }
