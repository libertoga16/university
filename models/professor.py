from odoo import models, fields, api

class UniversityProfessor(models.Model):
    _name = 'university.professor'
    _inherit = ['image.mixin']
    _description = 'University Professor'

    name = fields.Char(string='Name', required=True)
    university_id = fields.Many2one('university.university', string='University', required=True)
    department_ids = fields.Many2many('university.department', 'university_prof_dept_rel', 'prof_id', 'dept_id', string='Departments')
    subject_ids = fields.Many2many('university.subject', string='Subjects')
    enrollment_ids = fields.One2many('university.enrollment', 'professor_id', string='Enrollments')

    enrollment_count = fields.Integer(compute='_compute_counts', string='Enrollment Count')

    @api.depends('enrollment_ids')
    def _compute_counts(self):
        """
        Compute the number of enrollments associated with the professor.
        """
        for record in self:
            record.enrollment_count = self.env['university.enrollment'].search_count([('professor_id', '=', record.id)])
