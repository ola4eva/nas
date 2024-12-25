import time

from odoo import models, fields, api, _

from odoo.exceptions import ValidationError


class account_bank_statement_line(models.Model):
    _inherit = "account.bank.statement.line"
    _description = "St Line"

    cash_advance_id = fields.Many2one("cash.advance", string="Expense Advance")
    refund_advance_id = fields.Many2one("refund.advance", string="Refund Advance")


class cash_statement(models.Model):
    _inherit = "account.bank.statement"

    def button_confirm_cash(self):
        for c in self.line_ids:
            if (
                c.cash_advance_id
                and c.cash_advance_id.move_id1
                and c.cash_advance_id.move_id1.state == "draft"
            ):
                raise ValidationError(
                    "You cannot close this cash box. Please check and post draft journal entries created for this cash register for expense advances."
                )
            elif (
                c.refund_advance_id
                and c.refund_advance_id.move_id1
                and c.refund_advance_id.move_id1.state == "draft"
            ):
                raise ValidationError(
                    "You cannot close this cash box. Please check and post draft journal entries created for this cash register for advance refunds."
                )
        return super(cash_statement, self).button_confirm_cash()

    @api.model
    def fields_view_get(
        self, view_id=None, view_type="form", toolbar=False, submenu=False
    ):
        if view_type == "form" and self._context.get("advance_cash", False):
            result = self.env.ref("account.view_bank_statement_form2")
            view_id = result and result.id or False
        res = super(cash_statement, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=False
        )
        return res

    @api.model
    def create_move_from_st_line(self, st_line_id, company_currency_id, st_line_number):
        account_bank_statement_line_obj = self.env["account.bank.statement.line"]
        st_line = account_bank_statement_line_obj.browse(st_line_id)
        if (
            st_line.cash_advance_id or st_line.refund_advance_id
        ):  # not making journal entry for transfer transaction line on cash register..
            return True
        else:
            return super(cash_statement, self).create_move_from_st_line(
                st_line_id, company_currency_id, st_line_number
            )
