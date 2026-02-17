from odoo import models, fields, api

class Subject(models.Model):
    _name = 'university.subject'
    _description = 'Subject'

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', required=True)
    department_id = fields.Many2one('university.department', string='Department', required=True)
    university_id = fields.Many2one('university.university', related='department_id.university_id', string='University', store=True, readonly=True)
    professor_ids = fields.Many2many('university.professor', string='Professors')
    enrollment_ids = fields.One2many('university.enrollment', 'subject_id', string='Enrollments')

    enrollment_count = fields.Integer(compute='_compute_counts', string='Enrollment Count')

    @api.depends('enrollment_ids')
    def _compute_counts(self):
        """
        Compute the number of enrollments for the subject.
        """
        for record in self:
            record.enrollment_count = self.env['university.enrollment'].search_count([('subject_id', '=', record.id)])
