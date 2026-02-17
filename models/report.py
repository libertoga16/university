from odoo import models, fields, tools

class UniversityReport(models.Model):
    _name = 'university.report'
    _description = 'University Report'
    _auto = False
    _rec_name = 'student_id'

    university_id = fields.Many2one('university.university', string='University', readonly=True)
    professor_id = fields.Many2one('university.professor', string='Professor', readonly=True)
    department_id = fields.Many2one('university.department', string='Department', readonly=True)
    student_id = fields.Many2one('university.student', string='Student', readonly=True)
    subject_id = fields.Many2one('university.subject', string='Subject', readonly=True)
    score = fields.Float(string='Score', readonly=True, aggregator='avg')

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                    row_number() OVER () AS id,
                    u.id AS university_id,
                    p.id AS professor_id,
                    d.id AS department_id,
                    s.id AS student_id,
                    sub.id AS subject_id,
                    g.score AS score
                FROM
                    university_grade g
                JOIN
                    university_enrollment e ON g.enrollment_id = e.id
                JOIN
                    university_student s ON e.student_id = s.id
                JOIN
                    university_university u ON s.university_id = u.id
                JOIN
                    university_subject sub ON e.subject_id = sub.id
                LEFT JOIN
                    university_professor p ON e.professor_id = p.id
                LEFT JOIN
                    university_prof_dept_rel rel ON p.id = rel.prof_id
                LEFT JOIN
                    university_department d ON rel.dept_id = d.id
            )
        """ % (self._table))
