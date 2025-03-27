import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class HrContract(models.Model):
    _inherit = "hr.contract"

    skip_from_progress_action = fields.Boolean("Skip From Server Action")

    @api.model
    def start_contracts_except_skipped(self):
        contracts_to_start = self.search([]).filtered(
            lambda contract: not contract.skip_from_progress_action
        )
        _logger.info(f"Before: Contracts to be set to running... {contracts_to_start}")
        contracts_to_start and contracts_to_start.update({"state": "open"})
        contracts_to_start = self.search([]).filtered(
            lambda contract: not contract.skip_from_progress_action
        )
        _logger.info(f"After: Contracts to be set to running... {contracts_to_start}")
        return True
