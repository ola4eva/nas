from datetime import date

from odoo.exceptions import UserError

from odoo import api, fields, models


class AccountInvoice(models.Model):
    # @api.multi
    def action_invoice_open(self):
        # lots of duplicate calls to action_invoice_open, so we remove those already open
        to_open_invoices = self.filtered(lambda inv: inv.state != "open")
        if to_open_invoices.filtered(lambda inv: inv.state != "draft"):
            raise UserError(("Invoice must be in draft state in order to validate it."))
        if to_open_invoices.filtered(lambda inv: inv.amount_total < 0):
            raise UserError((
                    "You cannot validate an invoice with a negative total amount. You should create a credit note instead."
                )
            )
        to_open_invoices.action_date_assign()
        to_open_invoices.action_move_create()
        company_currency = self.company_id.currency_id
        current_currency = self.currency_id

        get_vat_tax = float(self.vat_tax.amount / 100 * self.amount_untaxed)
        print(get_vat_tax)
        amount = current_currency.compute(get_vat_tax, company_currency)
        print(amount)

        if self.journal_id.type == "sale":
            sign = 1
        else:
            sign = -1

        if self.journal_id.type == "purchase":
            sign = -1
        else:
            sign = 1
        if self.type == "out_invoice":
            a = {
                "name": str(self.number) + "/" + str(self.vat_tax.name),
                "date": date.today(),
                "ref": self.number,
                "company_id": self.env.user.company_id.id,
                "journal_id": self.journal_id.id,
                "state": "posted",
            }
            move_obj = self.env["account.move"].create(a)
            self.vat_journal_entry = move_obj.id
            b = {
                "name": self.vat_tax.name,
                "ref": self.name,
                "move_id": move_obj.id,
                "account_id": self.tax_expense_account_id.id,
                "credit": 0.0,
                "debit": amount,
                "journal_id": self.journal_id.id,
                "partner_id": self.partner_id.id,
                "currency_id": company_currency.id != current_currency.id and current_currency.id or False,
                "amount_currency": company_currency.id != current_currency.id and sign * get_vat_tax or 0.0,
                "date_maturity": date.today(),
            }
            c = {
                "name": self.vat_tax.name,
                "ref": self.name,
                "move_id": move_obj.id,
                "account_id": self.vat_tax.account_id.id,
                "credit": amount,
                "debit": 0.0,
                "journal_id": self.journal_id.id,
                "partner_id": self.partner_id.id,
                "currency_id": company_currency.id != current_currency.id and current_currency.id or False,
                "amount_currency": company_currency.id != current_currency.id and -sign * get_vat_tax or 0.0,
                "date_maturity": date.today(),
            }
            move_line_obj = self.env["account.move.line"].with_context(check_move_validity=False).create(b)
            move_line_obj = self.env["account.move.line"].with_context(check_move_validity=False).create(c)

        elif self.type == "in_invoice":
            account_line = []
            for con in self.invoice_line_ids:
                print(con.account_id.id)
                account_line.append(con.account_id.id)
            print(account_line)
            a = {
                "name": str(self.number) + "/" + str(self.vat_tax.name),
                "date_invoice": date.today(),
                "ref": self.number,
                "company_id": self.env.user.company_id.id,
                "journal_id": self.journal_id.id,
                "state": "posted",
            }
            move_obj = self.env["account.move"].create(a)
            self.vat_journal_entry = move_obj.id
            b = {
                "name": self.vat_tax.name,
                "ref": self.name,
                "move_id": move_obj.id,
                "account_id": account_line[0],
                "credit": 0.0,
                "debit": amount,
                "journal_id": self.journal_id.id,
                "partner_id": self.partner_id.id,
                "currency_id": company_currency.id != current_currency.id and current_currency.id or False,
                "amount_currency": company_currency.id != current_currency.id and -sign * get_vat_tax or 0.0,
                "date_maturity": date.today(),
            }
            c = {
                "name": self.vat_tax.name,
                "ref": self.name,
                "move_id": move_obj.id,
                "account_id": self.vat_tax.account_id.id,
                "credit": amount,
                "debit": 0.0,
                "journal_id": self.journal_id.id,
                "partner_id": self.partner_id.id,
                "currency_id": company_currency.id != current_currency.id and current_currency.id or False,
                "amount_currency": company_currency.id != current_currency.id and sign * get_vat_tax or 0.0,
                "date_maturity": date.today(),
            }
            move_line_obj = self.env["account.move.line"].with_context(check_move_validity=False).create(b)
            move_line_obj = self.env["account.move.line"].with_context(check_move_validity=False).create(c)

        return to_open_invoices.invoice_validate()

    _inherit = "account.move"
    add_vat = fields.Boolean("Add VAT", required=True, default=True)
    vat_tax = fields.Many2one("account.tax", "VAT")
    tax_expense_account_id = fields.Many2one("account.account", "Tax Expense Account")
    vat_journal_entry = fields.Many2one("account.move", "VAT Journal Entry", readonly=True)
