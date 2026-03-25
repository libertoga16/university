import logging

from odoo import models

_logger = logging.getLogger(__name__)

class BatchCountMixin(models.AbstractModel):
    """Efficient batch counting mixin for related records. N+1"""
    _name = 'batch.count.mixin'
    _description = 'Batch Count Mixin'

    def _get_batch_counts(self, model_name: str, field_name: str) -> dict[int, int]:
        """
        Calculates the count of records grouped by a relational field.
        
        Args:
            model_name (str): Target model name.
            field_name (str): Relational field to group by.

        Returns:
            dict[int, int]: Mapping of record IDs to their count.
        """
        if not self.ids:
            return {}

        domain = [(field_name, 'in', self.ids)]
        groups = self.env[model_name]._read_group(domain, [field_name], ['__count'])
        
        # We extract the ID from the relational record object (rel_record)
        return {rel_record.id: count for rel_record, count in groups if rel_record}