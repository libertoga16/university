import logging

from psycopg2 import sql as pgsql
from odoo import models, fields, tools

_logger = logging.getLogger(__name__)


class UniversityReport(models.Model):
    """Aggregated SQL view of student performance (Read-only)."""
    _name = 'university.report'
    _description = 'University Report'
    _auto = False  # no table
    _rec_name = 'student_id'

    university_id = fields.Many2one(
        comodel_name='university.university',
        string='University',
        readonly=True,
    )
    professor_id = fields.Many2one(
        comodel_name='university.professor',
        string='Professor',
        readonly=True,
    )
    department_id = fields.Many2one(
        comodel_name='university.department',
        string='Department',
        readonly=True,
    )
    student_id = fields.Many2one(
        comodel_name='university.student',
        string='Student',
        readonly=True,
    )
    subject_id = fields.Many2one(
        comodel_name='university.subject',
        string='Subject',
        readonly=True,
    )
    score = fields.Float(
        string='Average Score',
        readonly=True,
        aggregator='avg',
    )

    def init(self) -> None:
        """Initializes (or replaces) the SQL view backing this read-only report model."""
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(pgsql.SQL("""
            CREATE OR REPLACE VIEW {} AS (
                SELECT
                    e.id                AS id,
                    u.id                AS university_id,
                    p.id                AS professor_id,
                    d.id                AS department_id,
                    s.id                AS student_id,
                    sub.id              AS subject_id,
                    AVG(g.score)        AS score
                FROM university_enrollment e
                JOIN  university_student    s   ON s.id   = e.student_id
                JOIN  university_university u   ON u.id   = s.university_id
                JOIN  university_subject    sub ON sub.id = e.subject_id
                LEFT JOIN university_grade      g   ON g.enrollment_id = e.id
                LEFT JOIN university_professor  p   ON p.id = e.professor_id
                LEFT JOIN university_department d   ON d.id = p.department_id
                GROUP BY e.id, u.id, p.id, d.id, s.id, sub.id
            )
        """).format(pgsql.Identifier(self._table)))
