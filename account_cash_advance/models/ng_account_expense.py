import time

from odoo import models, fields, api, _

from odoo.exceptions import UserError, ValidationError


class refund_advance(models.Model):
    _name = "refund.advance"
    _inherit = ["mail.thread"]
    _description = "Refund Advance in Accounting"

    def approve(self):
        return self.write({"state": "approve"})

    def set_to_draft_app(self):
        return self.write({"state": "draft"})

    def set_to_draft(self):
        return self.write({"state": "draft"})

    def set_to_close(self):
        return self.write({"state": "reject"})

    def set_to_close_paid(self):
        return self.write({"state": "reject"})

    def set_to_cancel(self):
        return self.write({"state": "cancel"})

    def copy(self, default=None):
        if default is None:
            default = {}
        default.update(
            {
                "manager_id": False,
                "move_id1": False,
                "approval_date": False,
                "state": "draft",
            }
        )
        return super(refund_advance, self).copy(default)

    @api.model
    def _default_employee(self):
        ids = self.env["hr.employee"].search([("user_id", "=", self.env.user.id)])
        if ids:
            return ids[0]
        return False

    def create_move(self):
        #         period_obj = self.env['account.period']
        move_obj = self.env["account.move"]
        move_line_obj = self.env["account.move.line"]
        statement_line_obj = self.env["account.bank.statement.line"]
        currency_obj = self.env["res.currency"]

        ctx = dict(self._context or {})
        created_move_ids = []
        for line in self:
            if line.state == "paid":
                raise ValidationError("Accounting Moves already created.")
            if not line.journal_id:
                raise ValidationError("Please specify journal.")
            if not line.employee_account:
                raise ValidationError("Please specify employee account.")
            #             period_ids = period_obj.find(line.date)
            company_currency = line.company_id.currency_id
            current_currency = line.journal_id.currency_id
            flag = True
            if not current_currency:
                flag = False

            if not current_currency:
                current_currency = company_currency

            ctx.update({"date": line.date})
            if flag and current_currency != company_currency:
                amount_currency = company_currency.compute(
                    line.advance, current_currency
                )
            #                amount_currency = currency_obj.compute(company_currency, current_currency, line.advance)
            else:
                amount_currency = False

            res = current_currency.compute(line.advance, company_currency)

            ctx.update({"date": line.date})
            amount = current_currency.compute(line.advance, company_currency)
            if line.journal_id.type == "purchase":
                sign = 1
            else:
                sign = -1
            asset_name = line.name
            reference = line.name
            move_vals = {
                "date": line.date,
                "ref": reference,
                #                 'period_id': period_ids and period_ids.id or False,
                "journal_id": line.journal_id.id,
            }
            move_id = move_obj.create(move_vals)
            journal_id = line.journal_id.id
            if not line.journal_id.default_credit_account_id:
                raise ValidationError("Please specify account on journal.")
            address_id = line.emp_id.address_home_id or False
            if not address_id:
                raise ValidationError(
                    "There is no home address defined for employee: %s "
                ) % (_(line.emp_id.name))
            partner_id = address_id and address_id.id or False
            if not partner_id:
                raise ValidationError(
                    "There is no partner defined for employee : %s "
                ) % (_(line.emp_id.name))

            if line.update_cash:
                type = "general"
                amt = line.advance
                statement_line_obj.create(
                    {
                        "name": line.name or "?",
                        "amount": amt,
                        "type": type,
                        "account_id": line.employee_account.id,
                        "statement_id": line.cash_id.id,
                        "ref": line.name,
                        "partner_id": partner_id,
                        "date": time.strftime("%Y-%m-%d"),
                        "refund_advance_id": line.id,
                    }
                )
            sign = 1
            cr_line = []
            dr_line = []
            dr_line.append(
                (
                    0,
                    0,
                    {
                        "name": asset_name,
                        "ref": reference,
                        "move_id": move_id.id,
                        "account_id": line.journal_id.default_account_id.id,
                        "debit": res,
                        "credit": 0.0,
                        "journal_id": journal_id,
                        "partner_id": partner_id,
                        "currency_id": company_currency.id != current_currency.id
                        and current_currency.id
                        or False,
                        "amount_currency": flag
                        and company_currency.id != current_currency.id
                        and sign * line.advance
                        or 0.0,
                        "date": line.date,
                        "statement_id": line.cash_id and line.cash_id.id or False,
                    },
                )
            )
            sign = -1
            cr_line.append(
                (
                    0,
                    0,
                    {
                        "name": asset_name,
                        "ref": reference,
                        "move_id": move_id.id,
                        "account_id": line.employee_account.id,
                        "credit": res,
                        "debit": 0.0,
                        "journal_id": journal_id,
                        "partner_id": partner_id,
                        "currency_id": company_currency.id != current_currency.id
                        and current_currency.id
                        or False,
                        "amount_currency": flag
                        and company_currency.id != current_currency.id
                        and sign * line.advance
                        or 0.0,
                        "date": line.date,
                        "statement_id": line.cash_id and line.cash_id.id or False,
                    },
                )
            )
            final_list = cr_line + dr_line
            move_id.write({"line_ids": final_list})
            if line.refund_line:
                ramount = 0.0
                for rl in line.refund_line:
                    ramount = rl.ret_id.refund_amount + rl.amount
                    rl.ret_id.write({"refund_amount": ramount})

            created_move_ids.append(move_id)
            line.write({"move_id1": move_id.id, "state": "paid"})
        if self.emp_id.balance > self.advance:
            self.emp_id.balance = self.emp_id.balance - self.advance
        return True

    @api.model
    def _default_journal(self):
        return (
            self.env.user.company_id
            and self.env.user.company_id.ex_employee_journal
            and self.env.user.company_id.ex_employee_journal.id
            or False
        )

    @api.model
    def _default_account(self):
        return (
            self.env.user.company_id
            and self.env.user.company_id.ex_employee_account
            and self.env.user.company_id.ex_employee_account.id
            or False
        )

    name = fields.Char(
        string="Name",
        required=True,
        readonly=True,
        # states={"draft": [("readonly", False)]},
    )
    date = fields.Date(
        string="Refund Date",
        required=True,
        readonly=True,
        # states={"draft": [("readonly", False)]},
        default=time.strftime("%Y-%m-%d"),
    )
    emp_id = fields.Many2one(
        "hr.employee",
        string="Employee",
        required=True,
        readonly=True,
        # states={"draft": [("readonly", False)]},
        default=_default_employee,
    )
    department_id = fields.Many2one(
        related="emp_id.department_id", string="Department", readonly=True, store=True
    )
    advance = fields.Float(
        string="Refund Amount",
        required=True,
        readonly=True,
        # states={"draft": [("readonly", False)]},
    )
    state = fields.Selection(
        selection=[
            ("draft", "New"),
            ("approve", "Approved"),
            ("paid", "Refunded"),
            ("reject", "Rejected"),
            ("cancel", "Cancelled"),
        ],
        string="State",
        required=True,
        help="When an Advance Refund is created, the state is 'New'.\n"
        "If the CAdvance Refund is approved, the state goes in 'Approved' \n"
        "If the Advance Refund is refunded, the state goes in 'Refunded' \n"
        "If the Advance Refund is rejected, the state goes in 'Rejected' \n"
        "If the Advance Refund is cancelled, the state goes in 'Cancelled' \n",
        readonly=True,
        default="draft",
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        readonly=True,
        # states={"draft": [("readonly", False)]},
        default=lambda self: self.env["res.company"]._company_default_get(
            "refund.advance"
        ),
    )
    journal_id = fields.Many2one(
        "account.journal",
        string="Journal",
        domain="[('type','=','cash')]",
        # states={"paid": [("readonly", True)]},
        default=_default_journal,
    )
    currency_id = fields.Many2one(
        related="journal_id.currency_id",
        help="Payment in Multiple currency.",
        string="Currency",
        readonly=True,
    )
    move_id1 = fields.Many2one("account.move", string="Journal Entry", readonly=True)
    employee_account = fields.Many2one(
        "account.account",
        string="Employee Account",
        # states={"paid": [("readonly", True)]},
        default=_default_account,
    )

    notes = fields.Text(
        string="Description",
        # states={
        #     "paid": [("readonly", True)],
        #     "approve": [("readonly", True)],
        #     "cancel": [("readonly", True)],
        #     "reject": [("readonly", True)],
        # },
    )
    update_cash = fields.Boolean(
        string="Update Cash Register?",
        # states={"paid": [("readonly", True)]},
        help="Tick if you want to update cash register by creating cash transaction line.",
    )
    cash_id = fields.Many2one(
        "account.bank.statement",
        string="Cash Register",
        domain=[("journal_id.type", "in", ["cash"]), ("state", "=", "open")],
        required=False,
        # states={"paid": [("readonly", True)]},
    )

    refund_line = fields.One2many(
        "refund.line",
        "refund_id",
        string="Advance Lines",
        readonly=True,
        # states={"draft": [("readonly", False)]},
    ) 

    _order = "date desc, id desc"


class refund_line_ret_pay(models.Model):
    _name = "refund.line"
    _description = "Refund Lines"

    ret_id = fields.Many2one(
        "cash.advance",
        string="Expense Advance",
        ondelete="cascade",
        domain=[("state", "=", "paid")],
    )
    refund_id = fields.Many2one("refund.advance", string="Expense Refund")
    amount = fields.Float(string="Allocate Amount", readonly=False)
