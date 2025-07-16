import time
from odoo import models, fields, api, _, SUPERUSER_ID
from odoo.tools import float_compare
from odoo.exceptions import UserError, ValidationError

GROUP_CHECKER = "naseni_base.group_voucher_checker"
GROUP_AUDIT = "naseni_base.group_voucher_audit"
TEMPLATE_PREPARER = "account_cash_advance.preparer_notification_template"
TEMPLATE_CHECKER = "account_cash_advance.checker_notification_template"
TEMPLATE_AUDIT = "account_cash_advance.audit_notification_template"


class CashAdvance(models.Model):
    _name = "cash.advance"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Advances Request which requires retirements.."
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

    name = fields.Char(string="Number", default="/", required=True, readonly=True)
    description = fields.Char(
        string="Description",
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
        copy=False,
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
        related="emp_id.balance", string="Advance Balance", readonly=True
    )
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("open", "Submitted"),
            ("checked", "Checked"),
            ("audit", "Audit"),
            ("paid", "Posted"),
            ("rem", "Retired"),
            ("reject", "Rejected"),
            ("cancel", "Cancelled"),
        ],
        string="State",
        required=True,
        help="When an Advance Request is created, the state is 'New'.\n"
        "If the Advance Request is confirmed, the state goes in 'Confirmed' \n"
        "If the Advance Request is approved, the state goes in 'Approved' \n"
        "If the Advance Request is paid, the state goes in 'Paid' \n"
        "If the Advance Request Retired or reconciled with expense, the state goes in 'Retired' \n"
        "If the Advance Request is rejected, the state goes in 'Rejected' \n"
        "If the Advance Request is cancelled, the state goes in 'Cancelled' \n",
        readonly=True,
        copy=False,
        default="draft",
    )
    manager_id = fields.Many2one(
        "hr.employee",
        string="Approval Manager",
        readonly=True,
        copy=False,
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
    move_id1 = fields.Many2one(
        "account.move", string="Journal Entry", readonly=True, copy=False
    )
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
    ret_amount = fields.Float(string="Retired Amount", readonly=True)
    refund_amount = fields.Float(string="Refund Amount", readonly=True)  # #test
    amount_open = fields.Float(
        compute="_amount_all_open",
        help="Open Balance Amount After Retirements",
        string="Open Balance Amount",
        store=True,
    )  # need to call self.write when retirement fil and calcluate this fucntiona again
    prepared_by = fields.Many2one(comodel_name="res.users", string="Prepared By")
    prepared_on = fields.Datetime(string="Prepared On")
    checker_id = fields.Many2one(comodel_name="res.users", string="Checked By")
    checked_on = fields.Datetime(string="Checked On")
    auditor_id = fields.Many2one(comodel_name="res.users", string="Audited By")
    audited_on = fields.Datetime(string="Audited On")
    date_confirmed = fields.Date("Confirmation Date")
    voucher_type = fields.Selection(
        [
            ("capital", "Capital"),
            ("overhead", "Overhead"),
            ("advances", "Advances"),
        ],
        string="Voucher Type",
        tracking=True,
    )
    limit = fields.Float(
        string="Expense Limit", help="Limit amount of employee for expense advance.", related="emp_id.limit"
    )

    def validate(self):
        cash = self.with_user(user=SUPERUSER_ID)
        if not cash.advance:
            raise ValidationError(
                "You can not confirm cash advance if advance is zero."
            )
        if cash.amount_total + cash.emp_id.balance > cash.emp_id.limit:
            raise UserError(_("This advance request is over your allowed limit."))
        seq = self.env["ir.sequence"].next_by_code("cash.advance")

        # Notify the checker
        employee_id = self.env["hr.employee"].search(
            [("user_id", "=", self.env.uid)], limit=1
        )
        checker_group = self.env.ref(GROUP_CHECKER)
        self.send_notification(
            group_ids=checker_group.ids, template_id=TEMPLATE_CHECKER
        )

        return self.write(
            {
                "state": "open",
                "name": seq,
                "prepared_on": fields.Datetime.now(),
                "prepared_by": self._uid,
            }
        )

    def action_check(self):
        """Perform Checking..."""
        cash = self
        if cash.amount_total + cash.emp_id.balance > cash.emp_id.limit:
            raise ValidationError("This advance request is over your allowed limit.")
        date = time.strftime("%Y-%m-%d")
        obj_emp = self.env["hr.employee"]
        ids2 = obj_emp.search([("user_id", "=", self.env.user.id)], limit=1)
        manager = ids2 and ids2.id or False

        # Notify the auditor
        audit_group = self.env.ref(GROUP_AUDIT)
        self.send_notification(group_ids=audit_group.ids, template_id=TEMPLATE_AUDIT)

        return self.write(
            {
                "state": "checked",
                "manager_id": manager,
                "approval_date": date,
                "checker_id": self._uid,
                "checked_on": fields.Datetime.now(),
            }
        )

    def action_audit(self):
        """Perform Auditing..."""
        self.ensure_one()
        # Notify the auditor
        self.send_notification(user_ids=self.user_id.ids, template_id=TEMPLATE_AUDIT)
        return self.write(
            {
                "auditor_id": self._uid,
                "audited_on": fields.Datetime.now(),
                "state": "audit",
            }
        )

    def action_refuse(self):
        """Refuse the voucher."""
        self.ensure_one()
        return self.write({"state": "reject"})

    def set_to_draft_app(self):
        return self.write(
            {"state": "draft", "manager_id": False, "approval_date": False}
        )

    def unlink(self):
        """Override the unlink method to prevent deletion of records in certain states."""
        for record in self:
            if record.state != "draft":
                raise models.ValidationError(
                    "You cannot delete a record that is not in draft, submitted, checked or audit state."
                )
        return super(CashAdvance, self).unlink()

    def set_to_draft(self):
        return self.write(
            {"state": "draft", "manager_id": False, "approval_date": False}
        )

    def set_to_cancel(self):
        return self.write({"state": "cancel"})

    def _default_employee(self):
        ids = self.env["hr.employee"].search([("user_id", "=", self.env.user.id)])
        if ids:
            return ids[0]
        return False

    def create_move(self):
        move_obj = self.env["account.move"]
        statement_line_obj = self.env["account.bank.statement.line"]

        for advance in self:
            if not advance.move:
                continue
            if not advance.journal_id:
                raise ValidationError("Please specify a journal.")
            if not advance.employee_account:
                raise ValidationError("Please specify an employee account.")

            company_currency = advance.company_id.currency_id
            current_currency = advance.currency_id

            if not current_currency:
                current_currency = company_currency

            # Compute the amount in company currency
            move_vals = {
                "date": advance.date,
                "ref": advance.name,
                "journal_id": advance.journal_id.id,
            }
            move_id = move_obj.create(move_vals)

            # Ensure the journal has a default account
            if not advance.journal_id.default_account_id:
                raise UserError(_("Please specify an account on the journal."))

            address_id = advance.emp_id.address_home_id
            if not address_id:
                raise UserError(
                    _("There is no home address defined for employee: %s")
                    % advance.emp_id.name
                )
            partner_id = address_id.id

            if advance.update_cash:
                type = "general"
                statement_line_obj.create(
                    {
                        "name": advance.name or "?",
                        "amount": -(advance.advance),
                        "type": type,
                        "account_id": advance.employee_account.id,
                        "statement_id": advance.cash_id.id,
                        "ref": advance.name,
                        "partner_id": partner_id,
                        "date": time.strftime("%Y-%m-%d"),
                        "cash_advance_id": advance.id,
                    }
                )

            cr_line = [
                (
                    0,
                    0,
                    {
                        "name": advance.name,
                        "ref": advance.name,
                        "move_id": move_id.id,
                        "account_id": advance.journal_id.default_account_id.id,
                        "debit": 0.0,
                        "credit": advance.amount_total,
                        "partner_id": partner_id,
                        "currency_id": current_currency.id or False,
                        # "amount_currency":-amount_currency or 0.0,
                        "date": advance.date,
                        "statement_id": advance.cash_id.id or False,
                    },
                )
            ]
            dr_line = [
                (
                    0,
                    0,
                    {
                        "name": advance.name,
                        "ref": advance.name,
                        "move_id": move_id.id,
                        "account_id": advance.employee_account.id,
                        "credit": 0.0,
                        "debit": advance.amount_total,
                        "partner_id": partner_id,
                        "currency_id": current_currency.id or False,
                        # "amount_currency": company_currency != current_currency and amount_currency or 0.0,
                        "date": advance.date,
                        "statement_id": advance.cash_id.id or False,
                    },
                )
            ]
            final_list = cr_line + dr_line
            move_id.write({"line_ids": final_list})
            move_id.action_post()
            advance.write(
                {
                    "move_id1": move_id.id,
                    "state": "paid",
                    "date_confirmed": fields.Date.today(),
                }
            )
            rem = 0.0
            a = advance.emp_id.balance
            advance.emp_id.write(
                {"balance": advance.emp_id.balance + advance.amount_total}
            )
            if advance.expense_id and advance.expense_id.state == "paid":
                for x in advance.expense_id.line_ids:
                    rem += x.total_amount
            if advance.expense_id and advance.expense_id.state == "paid":
                advance.expense_id.write({"state": "rem"})
                ex = a + advance.advance - rem
                advance.write({"state": "rem", "ex_amount": ex})
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

    def send_notification(self, user_ids=None, group_ids=None, template_id=None):
        """Send notification to the groups that need to be informed

        Parameters
        ----------
        user_ids list:
            ids of the users to be notified. Mutually exclusive of the group_ids
        group_ids list:
            ids of the groups to be notified. Mutually exclusive of the user_ids
        template_id str:
            external identifier of the email templat to be used.

        """
        self.ensure_one()
        if not (user_ids or group_ids) or not template_id:
            return False
        template = self.env.ref(template_id)
        if group_ids:
            groups = self.env["res.groups"].browse(group_ids)
            users = groups.mapped("users")
        else:
            users = self.env["res.users"].browse(user_ids)
        return template.with_context(recipients=users).send_mail(
            self.id, force_send=True
        )
