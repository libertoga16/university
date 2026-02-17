from odoo import models, fields, api

class University(models.Model):
    _name = 'university.university'
    _inherit = ['image.mixin']
    _description = 'University'

    name = fields.Char(string='Name', required=True)
    street = fields.Char(string='Street')
    city = fields.Char(string='City')
    state_id = fields.Many2one('res.country.state', string='State')
    zip = fields.Char(string='Zip Code')
    country_id = fields.Many2one('res.country', string='Country')

    # Relational fields
    professor_ids = fields.One2many('university.professor', 'university_id', string='Professors')
    student_ids = fields.One2many('university.student', 'university_id', string='Students')
    enrollment_ids = fields.One2many('university.enrollment', 'university_id', string='Enrollments')
    department_ids = fields.One2many('university.department', 'university_id', string='Departments')

    # Computed fields for smart buttons
    professor_count = fields.Integer(compute='_compute_counts', string='Professor Count')
    student_count = fields.Integer(compute='_compute_counts', string='Student Count')
    enrollment_count = fields.Integer(compute='_compute_counts', string='Enrollment Count')
    department_count = fields.Integer(compute='_compute_counts', string='Department Count')

    @api.depends('professor_ids', 'student_ids', 'enrollment_ids', 'department_ids')
    def _compute_counts(self):
        """
        Compute the number of related records for the smart buttons.
        This method iterates over the recordset and calculates the length of each One2many field.
        """
        for record in self:
            record.professor_count = self.env['university.professor'].search_count([('university_id', '=', record.id)])
            record.student_count = self.env['university.student'].search_count([('university_id', '=', record.id)])
            record.enrollment_count = self.env['university.enrollment'].search_count([('university_id', '=', record.id)])
            record.department_count = self.env['university.department'].search_count([('university_id', '=', record.id)])
    