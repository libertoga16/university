import logging
from typing import Any, Dict, List, Optional

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class Department(models.Model):
    """
    Architectural entity representing a University Department.
    
    Organizes academic activities and personnel (professors) within a specific
    discipline or administrative unit.
    """
    _name = 'university.department'
    _inherit = ['batch.count.mixin']
    _description = 'Department'

    # === CORE FIELDS ===
    name = fields.Char(
        string='Name',
        required=True,
        index=True,
        help="Name of the department."
    )

    # === RELATIONAL FIELDS ===
    university_id = fields.Many2one(
        comodel_name='university.university',
        string='University',
        required=True,
        index=True,
        help="University this department belongs to."
    )
    manager_id = fields.Many2one(
        comodel_name='university.professor',
        string='Manager',
        index=True,
        help="Professor managing this department."
    )
    professor_ids = fields.Many2many(
        comodel_name='university.professor',
        relation='university_prof_dept_rel',
        column1='dept_id',
        column2='prof_id',
        string='Professors',
        help="Professors affiliated with this department."
    )

    # === COMPUTED FIELDS ===
    professor_count = fields.Integer(
        compute='_compute_counts',
        string='Professor Count',
        help="Number of professors in this department."
    )

    @api.depends('professor_ids')
    def _compute_counts(self) -> None:
        """
        Compute the number of professors in the department.
        """
        prof_map = self._get_batch_counts('university.professor', 'department_ids')
        for record in self:
            record.professor_count = prof_map.get(record.id, 0)

    def action_view_professors(self) -> Dict[str, Any]:
        """
        Open the list of professors for this department.

        Returns:
            Dict[str, Any]: Action dictionary to open the view.
        """
        self.ensure_one()
        return {
            'name': 'Professors',
            'type': 'ir.actions.act_window',
            'view_mode': 'kanban,list,form',
            'res_model': 'university.professor',
            'domain': [('department_ids', 'in', self.id)],
            'context': {'default_department_ids': [self.id]},
        }
