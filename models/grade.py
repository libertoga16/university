from odoo import models, fields, api

class Grade(models.Model):
    _name = 'university.grade'
    _description = 'Grade'

    enrollment_id = fields.Many2one('university.enrollment', string='Enrollment', required=True)
    student_id = fields.Many2one('university.student', related='enrollment_id.student_id', string='Student', store=True)
    score = fields.Float(string='Score')
    date = fields.Date(string='Date', default=fields.Date.context_today)

    def _compute_display_name(self):
        """
        Compute the display name for the grade.
        Format: [Student Name] - [Score]
        """
        for record in self:
            record.display_name = f"{record.student_id.name} - {record.score}"
