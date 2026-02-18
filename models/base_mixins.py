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

        result = {}
        for item in data:
            key = item[link_field]
            if isinstance(key, tuple):
                key = key[0]

            if key:
                result[key] = item[link_field + '_count']

        return result
