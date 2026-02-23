import logging
from typing import Dict, Any

from odoo import models, api

_logger = logging.getLogger(__name__)


class BatchCountMixin(models.AbstractModel):
    """
    Mixin to provide efficient batch counting of related records,
    eliminating N+1 query issues when computing counts.
    """
    _name = 'batch.count.mixin'
    _description = 'Batch Count Mixin'

    @api.model
    def _get_batch_counts(self, model_name: str, field_name: str) -> Dict[int, int]:
        """
        Compute counts of related records in batch.

        Args:
            model_name (str): The name of the related model (e.g., 'university.student').
            field_name (str): The Many2one field name linking back to self.

        Returns:
            Dict[int, int]: A mapping of record IDs to their computed counts.

        Example:
            counts = self._get_batch_counts('university.student', 'university_id')
        """
        if not self.ids:
            return {}

        domain = [(field_name, 'in', self.ids)]
        groups = self.env[model_name].read_group(
            domain=domain,
            fields=[field_name],  # read_group automatically computes <field>_count
            groupby=[field_name]
        )

        # Build mapping of ID -> Count
        result = {}
        for group in groups:
            # group[field_name] is typically a tuple (id, "name") for m2o
            val = group[field_name]
            record_id = val[0] if isinstance(val, tuple) else val
            if record_id:
                count_field = f"{field_name}_count"
                # If the groupby field count isn't in group (Odoo 16+ uses __count),
                # we handle it. Typically it's either <field>_count or __count
                count_val = group.get(count_field, group.get('__count', 0))
                result[record_id] = count_val

        return result
