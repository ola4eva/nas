from odoo import models, fields


class AccountMove(models.Model):
    _inherit = "account.move"

    def action_post(self):
        res = super(AccountMove, self).action_post()
        for record in self:
            if record.move_type == "in_invoice":
                print("What is the value of my record", record)
                # check if vendor bill is connected to payment requisition
                if request_id := self.env["payment.requisition"].search(
                    [("bill_ids", "in", record.ids)]
                ):
                    request_id._update_request_status()
        return res


class AccountMoveInherit(models.Model):
    _inherit = "account.move.line"

    customer_id = fields.Many2one(comodel_name="res.partner", string="Customer/Vendor")


class account_bank_statement_line(models.Model):
    _inherit = "account.bank.statement.line"

    payment_request_id = fields.Many2one(
        "payment.requisition", string="Payment Request"
    )
