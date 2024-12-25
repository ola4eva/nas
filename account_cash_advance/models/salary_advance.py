import time
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class SalaryAdvancePolicy(models.Model):
    _name = "salary.advance.policy"
    _description = "Salary Advance Policy Details"

    name = fields.Char(string="Name", required=True)
    day = fields.Char(
        string="Day of the Month",
        help="Select day of the month as starting point to allow salary advance to employee",
    )
    code = fields.Char(string="Code")
    employee_categ_ids = fields.Many2many(
        "hr.employee.category",
        "employee_category_policy_rel_sadvance",
        "policy_id",
        "category_id",
        "Employee Categories",
    )
    employee_ids = fields.Many2many(
        "hr.employee",
        "policy_employee_rel_sadvance",
        "policy_id",
        "employee_id",
        string="Employee's",
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        default=lambda self: self.env["res.company"]._company_default_get(
            "salary.advance.policy"
        ),
    )
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("done", "Done"),
        ],
        string="State",
        readonly=True,
    )
    method = fields.Selection(
        selection=[
            ("basic", "% of Basic Salary"),
            ("gross", "% of Gross Salary"),
            ("fixed", "Fix Amount"),
            ("", ""),
        ],
        string="Basis",
        help="As a percentage of Basic/Gross Salary or as a fixed amount",
    )
    policy_value = fields.Float(
        string="Value",
        help="If policy type is Basis is Gross/Basic, then set value as a ratio between 0 and 1 as %. If Basis is Fixed Amount, then set value as a fixed amount.",
    )


class AccountSalaryAdvance(models.Model):
    _name = "salary.advance"
    _description = "Salary Advance to employee"
    _order = "date desc, id desc"
    _inherit = ["mail.thread"]

    def _valid_field_parameter(self, field, name):
        return name == "states" or super()._valid_field_parameter(field, name)

    def validate(self):
        domain1 = [
            ("employee_id", "=", self.emp_id.id),
            ("contract_id", "=", self.emp_id.contract_id.id),
            ("code", "=", "NET"),
        ]
        line_ids = self.env["hr.payslip.line"].search(domain1, limit=1)
        net_amount = False
        if not self.advance:
            raise ValidationError(
                "You can not confirm salary advance if advance is zero."
            )
        if line_ids:
            line = line_ids
            net_amount = line.amount

            if self.advance > net_amount:
                raise ValidationError(
                    "You can not take advance of this amount as your NET salary seems going negative."
                )
        for categ in self.emp_id.category_ids:
            if categ.salary_advance_policy:
                for p in categ.salary_advance_policy:

                    ds = datetime.strptime(self.date, "%Y-%m-%d")
                    if ds.day <= int(p.day):
                        raise ValidationError(
                            _("Warning !"),
                            _(
                                "You can not take advance in current date as policy does not allow you to take advance before specific day."
                            ),
                        )
                    if p.method == "fixed" and p.policy_value < self.advance:
                        raise ValidationError(
                            _("Warning !"),
                            _(
                                "You are exceeding the limit of advance as salary advance policy set for : %s not allowed."
                            )
                            % (_(self.emp_id.name)),
                        )
                    if p.method == "basic":
                        w = self.emp_id.contract_id.wage
                        if w:
                            pamount = w * p.policy_value
                            if self.advance > pamount:
                                raise ValidationError(
                                    _("Warning !"),
                                    _(
                                        "You are exceeding the limit of advance as salary advance policy set for : %s not allowed."
                                    )
                                    % (_(self.emp_id.name)),
                                )
                    if p.method == "gross":
                        domain = [
                            ("employee_id", "=", self.emp_id.id),
                            ("contract_id", "=", self.emp_id.contract_id.id),
                            ("code", "=", "GROSS"),
                        ]
                        line_ids = self.env["hr.payslip.line"].search(domain, limit=1)
                        if line_ids:
                            line = line_ids
                            gross_amount = line.amount
                            gross_amount = line.amount * p.policy_value
                        if gross_amount < self.advance:
                            raise ValidationError(
                                _("Warning !"),
                                _(
                                    "You are exceeding the limit of advance as salary advance policy set for : %s not allowed."
                                )
                                % (_(self.emp_id.name)),
                            )

        for p in self.emp_id.salary_advance_policy:
            ds = datetime.strptime(self.date, "%Y-%m-%d")
            if ds.day <= int(p.day):
                raise ValidationError(
                    _("Warning !"),
                    _(
                        "You can not take advance in current date as policy does not allow you to take advance before specific day."
                    ),
                )
            if p.method == "fixed" and p.policy_value < self.advance:
                raise ValidationError(
                    _("Warning !"),
                    _(
                        "You are exceeding the limit of advance as salary advance policy set for : %s not allowed."
                    )
                    % (_(self.emp_id.name)),
                )
            if p.method == "basic":
                w = self.emp_id.contract_id.wage
                if w:
                    pamount = w * p.policy_value
                    if self.advance > pamount:
                        raise ValidationError(
                            _("Warning !"),
                            _(
                                "You are exceeding the limit of advance as salary advance policy set for : %s not allowed."
                            )
                            % (_(self.emp_id.name)),
                        )
            if p.method == "gross":
                domain = [
                    ("employee_id", "=", self.emp_id.id),
                    ("contract_id", "=", self.emp_id.contract_id.id),
                    ("code", "=", "GROSS"),
                ]
                line_ids = self.env["hr.payslip.line"].search(domain, limit=1)
                if line_ids:
                    line = line_ids
                    gross_amount = line.amount
                    gross_amount = line.amount * p.policy_value
                if gross_amount < self.advance:
                    raise ValidationError(
                        _("Warning !"),
                        _(
                            "You are exceeding the limit of advance as salary advance policy set for : %s not allowed."
                        )
                        % (_(self.emp_id.name)),
                    )
        return self.write({"state": "open"})

    def approve(self):
        date = time.strftime("%Y-%m-%d")
        obj_emp = self.env["hr.employee"]
        ids2 = obj_emp.search([("user_id", "=", self.env.user.id)], limit=1)
        manager = ids2 and ids2.id or False
        return self.write(
            {
                "state": "approve",
                "manager_id": manager,
                "approval_date": date,
                "date_valid": time.strftime("%Y-%m-%d"),
            }
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
        return super(account_salary_advance, self).copy(default)

    @api.model
    def _default_employee(self):
        ids = self.env["hr.employee"].search(
            [("user_id", "=", self.env.user.id)], limit=1
        )
        if ids:
            return ids

    def create_move(self):
        #         period_obj = self.env['account.period']
        move_obj = self.env["account.move"]
        move_line_obj = self.env["account.move.line"]
        created_move_ids = []

        ctx = dict(self._context or {})

        for line in self:
            if not line.move:
                continue
            if line.state == "paid":
                raise ValidationError(_("Accounting Moves already created."))
            if not line.journal_id:
                raise ValidationError(_("Please specify journal."))
            if not line.employee_account:
                raise ValidationError(_("Please specify employee account."))

            #             period_ids = period_obj.find(line.date)
            company_currency = line.company_id.currency_id
            current_currency = line.journal_id.currency_id
            flag = True
            if not current_currency:
                flag = False

            ctx.update({"date": line.date})

            if flag and current_currency.id != company_currency.id:
                amount_currency = company_currency.compute(
                    line.advance, current_currency
                )
            else:
                amount_currency = False

            if not current_currency:
                current_currency = company_currency
            res = current_currency.compute(line.advance, company_currency)

            ctx.update({"date": line.date})
            amount = current_currency.compute(line.advance, company_currency)
            sign = 1 if line.journal_id.type in ("purchase") else -1

            asset_name = line.name
            reference = line.name
            move_vals = {
                #                'name': asset_name,
                "date": line.date,
                "ref": reference,
                #                 'period_id': period_ids and period_ids.id or False,
                "journal_id": line.journal_id.id,
            }
            move_id = move_obj.create(move_vals)
            journal_id = line.journal_id.id
            #            partner_id = line.asset_id.partner_id.id
            if not line.journal_id.default_credit_account_id:
                raise ValidationError(_("Please specify account on journal."))
            address_id = line.emp_id.address_home_id or False
            if not address_id:
                raise ValidationError(
                    _("There is no home address defined for employee: %s ")
                    % (_(line.emp_id.name))
                )
            partner_id = address_id and address_id.id or False
            if not partner_id:
                raise ValidationError(
                    _("There is no partner defined for employee : %s ")
                    % (_(line.emp_id.name))
                )
            sign = -1

            cr_line = []
            dr_line = []
            cr_line.append(
                (
                    0,
                    0,
                    {
                        "name": asset_name,
                        "ref": reference,
                        "move_id": move_id.id,
                        "account_id": line.journal_id.default_account_id.id,
                        "debit": 0.0,
                        "credit": res,
                        #                 'period_id': period_ids and period_ids.id or False,
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
                    },
                )
            )
            sign = 1
            dr_line.append(
                (
                    0,
                    0,
                    {
                        "name": asset_name,
                        "ref": reference,
                        "move_id": move_id.id,
                        "account_id": line.employee_account.id,
                        "credit": 0.0,
                        "debit": res,
                        #                 'period_id': period_ids and period_ids.id or False,
                        "journal_id": journal_id,
                        "partner_id": partner_id,
                        "currency_id": company_currency.id != current_currency.id
                        and current_currency.id
                        or False,
                        "amount_currency": flag
                        and company_currency.id != current_currency.id
                        and sign * line.advance
                        or 0.0,
                        #                'analytic_account_id': line.asset_id.category_id.account_analytic_id.id,
                        "date": line.date,
                    },
                )
            )
            final_list = cr_line + dr_line
            move_id.write({"line_ids": final_list})
            #            self.write(cr, uid, line.id, {'move_id': move_id}, context=context)
            created_move_ids.append(move_id.id)
            line.write({"move_id1": move_id.id})
        line.write({"state": "paid"})
        return True

    @api.model
    def _default_journal(self):
        return (
            self.env.user.company_id
            and self.env.user.company_id.cash_employee_journal
            and self.env.user.company_id.cash_employee_journal
        )

    @api.model
    def _default_account(self):
        return (
            self.env.user.company_id
            and self.env.user.company_id.cash_employee_account
            and self.env.user.company_id.cash_employee_account
        )

    name = fields.Char(
        string="Name",
        required=True,
        readonly=True,
        #    states={'draft':[('readonly', False)]}
    )
    date = fields.Date(
        string="Request Date",
        required=True,
        readonly=True,
        #    states={'draft':[('readonly', False)]},
        default=time.strftime("%Y-%m-%d"),
    )
    approval_date = fields.Date(
        string="Approve Date",
        readonly=True,
        # states={'approve':[('readonly', True)], 'cancel':[('readonly', True)], 'reject':[('readonly', True)]}
    )
    emp_id = fields.Many2one(
        "hr.employee",
        string="Employee",
        required=True,
        readonly=True,
        #  states={'draft':[('readonly', False)]},
        default=_default_employee,
    )
    user_id = fields.Many2one(
        related="emp_id.user_id",
        readonly=True,
        # states={"draft": [("readonly", False)]},
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
        # states={"draft": [("readonly", False)]},
    )
    state = fields.Selection(
        selection=[
            ("draft", "New"),
            ("open", "Confirmed"),
            ("approve", "Approved"),
            ("paid", "Paid"),
            ("reject", "Rejected"),
            ("cancel", "Cancelled"),
        ],
        string="State",
        required=True,
        help="When an Advance is created, the state is 'New'.\n"
        "If the Advance is confirmed, the state goes in 'Confirmed' \n"
        "If the Advance is approved, the state goes in 'Approved' \n"
        "If the Advance is paid, the state goes in 'Paid' \n"
        "If the Advance is rejected, the state goes in 'Rejected' \n"
        "If the Advance is cancelled, the state goes in 'Cancelled' \n",
        default="draft",
    )
    manager_id = fields.Many2one(
        "hr.employee",
        string="Approval Manager",
        readonly=True,
        help="This area is automatically filled by the user who validate the salary advance",
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
        default=lambda self: self.env["res.company"]._company_default_get(
            "salary.advance"
        ),
    )
    move = fields.Boolean(
        string="Create Journal Entry?",
        # states={"paid": [("readonly", True)]},
        help="Tick if you want to raise journal entry when you click pay button",
        default=True,
    )
    journal_id = fields.Many2one(
        "account.journal",
        "Journal",
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
        domain="[('account_type','=','receivable')]",
        # states={"paid": [("readonly", True)]},
        default=_default_account,
    )
    notes = fields.Text(
        string="Notes",
        # states={
        #     "paid": [("readonly", True)],
        #     "approve": [("readonly", True)],
        #     "cancel": [("readonly", True)],
        #     "reject": [("readonly", True)],
        # },
    )
