import logging
from typing import Dict

from odoo import models, api

_logger = logging.getLogger(__name__)

class BatchCountMixin(models.AbstractModel):
    """
    Mixin to provide efficient batch counting of related records using Odoo 19 _read_group.
    """
    _name = 'batch.count.mixin'
    _description = 'Batch Count Mixin'

    @api.model
    def _get_batch_counts(self, model_name: str, field_name: str) -> Dict[int, int]:
        if not self.ids:
            return {}

        domain = [(field_name, 'in', self.ids)]
        # Odoo 19 standard: _read_group(domain, groupby, aggregates)
        # Returns a list of tuples: [(groupby_record_or_value, aggregate_value), ...]
        groups = self.env[model_name]._read_group(domain, [field_name], ['__count'])
        
        # In Odoo 19, relational groupbys return the recordset directly, not just the ID.
        return {rel_record.id: count for rel_record, count in groups if rel_record}
