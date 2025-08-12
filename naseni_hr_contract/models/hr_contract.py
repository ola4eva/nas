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

    @api.model
    def _cron_update_contract_start_date(self, step=50):
        def splittor(rs):
            for idx in range(0, len(rs)):
                sub = rs[idx : idx + step]
                for rec in sub:
                    yield rec
                self._invalidate_cache(ids=sub.ids)

        contracts_to_update = self.search([("state", "=", "draft")]).filtered(
            lambda contract: contract.date_start != contract.employee_id.date_present
            and contract.employee_id.date_present != False
        )
        contracts_to_update = self.search([]).filtered(
            lambda contract: contract.date_start != contract.employee_id.date_present
            and contract.employee_id.date_present != False
        )
        for contract in splittor(contracts_to_update):
            contract._update_contract_start_date()
        return True

    def _update_contract_start_date(self):
        """Update the contract start date for single record"""
        for contract in self:
            if not contract.employee_id.date_present:
                continue
            _logger.info(
                f"Start Date Before Updating: Contracts to be set to running... {contract.date_start}"
            )
            try:
                contract.update({"date_start": contract.employee_id.date_present})
            except Exception as e:
                _logger.error("Unable to update the start date")
            _logger.info(
                f"After: Contracts to be set to running... {contract.date_start}"
            )
