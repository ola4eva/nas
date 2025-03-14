import time

from odoo import models, fields, api, _, SUPERUSER_ID
from odoo.tools import float_compare
from odoo.exceptions import UserError, ValidationError


class account_cash_advance(models.Model):
    _name = "cash.advance"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Cash Advance for expense later he will fill retirements.."
    _order = "date desc, id desc"

    @api.model
    def _default_journal(self):
        return (
            self.env.user.company_id
            and self.env.user.company_id.ex_employee_journal
            and self.env.user.company_id.ex_employee_journal
        )

    @api.model
    def _default_account(self):
        return (
            self.env.user.company_id
            and self.env.user.company_id.ex_employee_account
            and self.env.user.company_id.ex_employee_account
        )

    def _default_currency_id(self):
        res = False
        if self.env.user:
            res = (
                self.env.user
                and self.env.user.company_id
                and self.env.user.company_id.currency_id
            )
        return res

    def _default_emp_id(self):
        return self.env["hr.employee"].search(
            [("user_id", "=", self.env.user.id)], limit=1
        )

    name = fields.Char(
        string="Expense Description",
        required=True,
        readonly=False,
    )
    date = fields.Date(
        string="Request Date",
        required=True,
        readonly=True,
        default=time.strftime("%Y-%m-%d"),
    )
    approval_date = fields.Date(
        string="Approve Date",
        readonly=True,
    )
    emp_id = fields.Many2one(
        "hr.employee",
        string="Employee",
        required=True,
        default=_default_emp_id,
    )
    user_id = fields.Many2one(
        related="emp_id.user_id",
        readonly=True,
        string="User",
        store=True,
    )
    department_id = fields.Many2one(
        related="emp_id.department_id", string="Department", readonly=True, store=True
    )
    advance = fields.Float(
        string="Amount",
        required=True,
        readonly=True,
    )
    ex_amount = fields.Float(
        string="Extra Amount",
        required=False,
        readonly=True,
    )
    balance = fields.Float(
        related="emp_id.balance", string="Expense Advance Balance", readonly=True
    )
    state = fields.Selection(
        selection=[
            ("draft", "New"),
            ("open", "Confirmed"),
            ("approve", "Approved"),
            ("paid", "Paid"),
            ("rem", "Retired"),
            ("reject", "Rejected"),
            ("cancel", "Cancelled"),
        ],
        string="State",
        required=True,
        help="When an Cash Advance is created, the state is 'New'.\n"
        "If the Cash Advance is confirmed, the state goes in 'Confirmed' \n"
        "If the Cash Advance is approved, the state goes in 'Approved' \n"
        "If the Cash Advance is paid, the state goes in 'Paid' \n"
        "If the Cash Advance Retired or reconciled with expense, the state goes in 'Retired' \n"
        "If the Cash Advance is rejected, the state goes in 'Rejected' \n"
        "If the Cash Advance is cancelled, the state goes in 'Cancelled' \n",
        readonly=True,
        default="draft",
    )
    manager_id = fields.Many2one(
        "hr.employee",
        string="Approval Manager",
        readonly=True,
        help="This area is automatically filled by the user who validate the cash advance",
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        readonly=True,
        default=lambda self: self.env["res.company"]._company_default_get(
            "cash.advance"
        ),
    )
    move = fields.Boolean(
        string="Create Journal Entry?",
        help="Tick if you want to raise journal entry when you click pay button",
        default=True,
    )
    journal_id = fields.Many2one(
        "account.journal",
        string="Journal",
        domain="['|', ('type','=','cash'), ('type','=','bank')]",
        default=_default_journal,
    )
    move_id1 = fields.Many2one("account.move", string="Journal Entry", readonly=True)
    expense_id = fields.Many2one(
        "ret.expense",
        string="Expense",
    )
    employee_account = fields.Many2one(
        comodel_name="account.account",
        string="Ledger Account",
        default=_default_account,
    )
    notes = fields.Text(
        string="Description",
    )

    update_cash = fields.Boolean(
        string="Update Cash Register?",
        help="Tick if you want to update cash register by creating cash transaction line.",
    )
    cash_id = fields.Many2one(
        "account.bank.statement",
        string="Cash Register",
        domain=[("journal_id.type", "in", ["cash"]), ("state", "=", "open")],
        required=False,
    )

    currency_id = fields.Many2one(
        "res.currency", string="Currency", required=True, default=_default_currency_id
    )
    amount_total = fields.Float(
        compute="_amount_all",
        help="Amount in company currency.",
        string="Equivalent Amount",
        store=True,
    )
    # sat
    ret_amount = fields.Float(string="Retired Amount", readonly=True)
    refund_amount = fields.Float(string="Refund Amount", readonly=True)  # #test
    amount_open = fields.Float(
        compute="_amount_all_open",
        help="Open Balance Amount After Retirements",
        string="Open Balance Amount",
        store=True,
    )  # need to call self.write when retirement fil and calcluate this fucntiona again

    def validate(self):
        cash = self.with_user(user=SUPERUSER_ID)
        if not cash.advance:
            raise ValidationError(
                "You can not confirm cash advance if advance is zero."
            )
        if cash.amount_total + cash.emp_id.balance > cash.emp_id.limit:
            raise UserError(_("This advance request is over your allowed limit."))
        return self.write({"state": "open"})

    def approve(self):
        cash = self
        if cash.amount_total + cash.emp_id.balance > cash.emp_id.limit:
            raise ValidationError("This advance request is over your allowed limit.")
        date = time.strftime("%Y-%m-%d")
        obj_emp = self.env["hr.employee"]
        ids2 = obj_emp.search([("user_id", "=", self.env.user.id)], limit=1)
        manager = ids2 and ids2.id or False
        return self.write(
            {"state": "approve", "manager_id": manager, "approval_date": date}
        )

    def set_to_draft_app(self):
        return self.write(
            {"state": "draft", "manager_id": False, "approval_date": False}
        )

    def set_to_draft(self):
        return self.write(
            {"state": "draft", "manager_id": False, "approval_date": False}
        )

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
        return super(account_cash_advance, self).copy(default)

    def _default_employee(self):
        ids = self.env["hr.employee"].search([("user_id", "=", self.env.user.id)])
        if ids:
            return ids[0]
        return False

    def create_move(self):
        move_obj = self.env["account.move"]
        statement_line_obj = self.env["account.bank.statement.line"]
        created_move_ids = []

        for line in self:
            if not line.move:
                continue
            if not line.journal_id:
                raise ValidationError("Please specify a journal.")
            if not line.employee_account:
                raise ValidationError("Please specify an employee account.")

            company_currency = line.company_id.currency_id
            current_currency = line.currency_id
            flag = bool(current_currency)

            if not current_currency:
                current_currency = company_currency

            # Compute the amount in company currency
            amount_currency = 0.0
            if flag and current_currency != company_currency:
                amount_currency = company_currency._convert(
                    line.advance, current_currency, line.company_id, line.date
                )

            move_vals = {
                "date": line.date,
                "ref": line.name,
                "journal_id": line.journal_id.id,
            }
            move_id = move_obj.create(move_vals)

            # Ensure the journal has a default account
            if not line.journal_id.default_account_id:
                raise UserError(_("Please specify an account on the journal."))

            address_id = line.emp_id.address_home_id
            if not address_id:
                raise UserError(
                    _("There is no home address defined for employee: %s")
                    % line.emp_id.name
                )
            partner_id = address_id.id

            if line.update_cash:
                type = "general"
                amt = -(line.advance)
                statement_line_obj.create(
                    {
                        "name": line.name or "?",
                        "amount": -(line.advance),
                        "type": type,
                        "account_id": line.employee_account.id,
                        "statement_id": line.cash_id.id,
                        "ref": line.name,
                        "partner_id": partner_id,
                        "date": time.strftime("%Y-%m-%d"),
                        "cash_advance_id": line.id,
                    }
                )

            cr_line = [
                (
                    0,
                    0,
                    {
                        "name": line.name,
                        "ref": line.name,
                        "move_id": move_id.id,
                        "account_id": line.journal_id.default_account_id.id,
                        "debit": 0.0,
                        "credit": line.amount_total,
                        "partner_id": partner_id,
                        "currency_id": current_currency.id or False,
                        # "amount_currency":-amount_currency or 0.0,
                        "date": line.date,
                        "statement_id": line.cash_id.id or False,
                    },
                )
            ]
            dr_line = [
                (
                    0,
                    0,
                    {
                        "name": line.name,
                        "ref": line.name,
                        "move_id": move_id.id,
                        "account_id": line.employee_account.id,
                        "credit": 0.0,
                        "debit": line.amount_total,
                        "partner_id": partner_id,
                        "currency_id": current_currency.id or False,
                        # "amount_currency": company_currency != current_currency and amount_currency or 0.0,
                        "date": line.date,
                        "statement_id": line.cash_id.id or False,
                    },
                )
            ]
            final_list = cr_line + dr_line
            move_id.write({"line_ids": final_list})

            created_move_ids.append(move_id)
            line.write({"move_id1": move_id.id, "state": "paid"})
            rem = 0.0
            a = line.emp_id.balance
            line.emp_id.write({"balance": line.emp_id.balance + line.amount_total})
            if line.expense_id and line.expense_id.state == "paid":
                for x in line.expense_id.line_ids:
                    rem += x.total_amount
            if line.expense_id and line.expense_id.state == "paid":
                line.expense_id.write({"state": "rem"})
                ex = a + line.advance - rem
                line.write({"state": "rem", "ex_amount": ex})

        return True

    @api.depends("company_id", "advance")
    def _amount_all(self):
        for cash in self:
            company_currency = cash.company_id.currency_id
            # Use _convert instead of the deprecated compute method
            cur_amt = cash.currency_id._convert(
                cash.advance,
                company_currency,
                cash.company_id,
                cash.date or fields.Date.today(),
            )

            cash.amount_total = cur_amt
            print("_amount_all", cash.amount_total)

    @api.depends("amount_total", "ret_amount", "refund_amount")
    def _amount_all_open(self):  # sat
        self.amount_open = (
            self.amount_total - self.ret_amount - self.refund_amount
        )  # test

    def _get_associated_reconcile_lines(self):
        """Check if the cash advance has any associated retirements.

        Returns
        -------
            bool
                True if the advance is has_retirements, False otherwise.
        """
        for record in self:
            reconcile_lines = self.env["ret.expense.reconcile"].search(
                [("ret_id", "=", record.id)]
            )
            retirement_ids = reconcile_lines.mapped("ref_id")
            return retirement_ids.line_ids

    def is_fully_retired(self):
        """
        Check if the advance is fully retired.

        Returns
        -------
        bool
            True if the advance is fully retired, False otherwise.
        """
        for rec in self:
            if not rec._get_associated_reconcile_lines():
                return False
            line_ids = rec._get_associated_reconcile_lines()
            # check if the total of the cash advance and the total retirements are equal
            # and all retirements are in done state
            if (
                float_compare(rec.amount_total, sum(line_ids.mapped("total_amount")), 2)
                == 0
                and line_ids.mapped("expense_id").state == "paid"
            ):
                return True
            return False

    @api.model
    def set_unretired_advances_to_retired(self):
        """Check non-retired advances and set to 'retired'."""
        non_retired_advances = self.search([("state", "!=", "rem")])
        advances_valid_for_retirement = non_retired_advances.filtered(
            lambda nra: nra.is_fully_retired()
        )
        advances_valid_for_retirement and advances_valid_for_retirement.update(
            {"state": "rem"}
        )
        return True
