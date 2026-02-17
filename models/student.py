from odoo import models, fields, api

class UniversityStudent(models.Model):
    _name = 'university.student'
    _inherit = ['image.mixin']
    _description = 'University Student'

    name = fields.Char(string='Name', required=True)
    university_id = fields.Many2one('university.university', string='University', required=True)
    
    street = fields.Char(string='Street')
    city = fields.Char(string='City')
    state_id = fields.Many2one('res.country.state', string='State')
    zip = fields.Char(string='Zip Code')
    country_id = fields.Many2one('res.country', string='Country')
    
    tutor_id = fields.Many2one('university.professor', string='Tutor')
    
    enrollment_ids = fields.One2many('university.enrollment', 'student_id', string='Enrollments')
    grade_ids = fields.One2many('university.grade', 'student_id', string='Grades')

    enrollment_count = fields.Integer(compute='_compute_counts', string='Enrollment Count')
    grade_count = fields.Integer(compute='_compute_counts', string='Grade Count')

    @api.depends('enrollment_ids', 'grade_ids')
    def _compute_counts(self):
        """
        Compute the number of enrollments and grades for the student.
        """
        for record in self:
            record.enrollment_count = self.env['university.enrollment'].search_count([('student_id', '=', record.id)])
            record.grade_count = self.env['university.grade'].search_count([('student_id', '=', record.id)])
