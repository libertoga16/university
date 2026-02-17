from odoo import models, fields, api

class Department(models.Model):
    _name = 'university.department'
    _description = 'Department'

    name = fields.Char(string='Name', required=True)
    university_id = fields.Many2one('university.university', string='University', required=True)
    manager_id = fields.Many2one('university.professor', string='Manager')
    professor_ids = fields.Many2many('university.professor', 'university_prof_dept_rel', 'dept_id', 'prof_id', string='Professors')

    professor_count = fields.Integer(compute='_compute_counts', string='Professor Count')

    @api.depends('professor_ids')
    def _compute_counts(self):
        """
        Compute the number of professors in the department.
        """
        for record in self:
            record.professor_count = self.env['university.professor'].search_count([('department_ids', 'in', record.id)])

    def action_view_professors(self):
        self.ensure_one()
        return {
            'name': 'Professors',
            'type': 'ir.actions.act_window',
            'view_mode': 'kanban,list,form',
            'res_model': 'university.professor',
            'domain': [('department_ids', 'in', self.id)],
            'context': {'default_department_ids': [self.id]},
        }
