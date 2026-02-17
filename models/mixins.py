from typing import Any, Dict, List, Optional
from odoo import models, api

class BatchCountMixin(models.AbstractModel):
    _name = 'batch.count.mixin'
    _description = 'Mixin for optimized batch counting'

    def _get_batch_counts(self, target_model: str, link_field: str, domain: Optional[List[Any]] = None) -> Dict[int, int]:
        """
        Generic optimized counter using read_group.
        
        :param target_model: Model name to count (e.g., 'university.student')
        :param link_field: Foreign key field name in target_model (e.g., 'university_id')
        :param domain: Optional extra domain (e.g., [('state', '=', 'done')])
        :return: Dict {record_id: count}
        """
        if not self:
            return {}

        base_domain = [(link_field, 'in', self.ids)]
        if domain:
            base_domain += domain

        data = self.env[target_model].read_group(
            domain=base_domain,
            fields=[link_field],
            groupby=[link_field]
        )
        
        # Determine if the link_field is a relational field (tuple) or simple value
        # read_group on Many2one/Many2many usually returns {field: (id, name), field_count: count}
        # But we need to handle cases carefully. 
        # For M2O, item[link_field] is (id, name).
        # For M2M, it might be similar if grouped by it.
        
        result = {}
        for item in data:
            key = item[link_field]
            # Handle (id, name) tuple from Many2one/Many2many grouping
            if isinstance(key, tuple):
                key = key[0]
            
            if key: # Ensure we don't map None/False keys
                result[key] = item[link_field + '_count']
                
        return result
