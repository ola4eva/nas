from odoo import models, fields, api, _
from datetime import date
from odoo.exceptions import ValidationError


class hr_expense_expense_ret(models.Model):

    _name = "ret.expense"
    _description = "Retirements Expense"
    _order = "date desc, id desc"
    _inherit = ["mail.thread"]

    def _valid_field_parameter(self, field, name):
        return name == "states" or super()._valid_field_parameter(field, name)

    def validate(self):
        return self.write({"state": "open", "date_confirm": date.today()})

    def approve(self):
        return self.write({"state": "approve", "user_valid": self.env.user.id})

    def set_to_draft_app(self):
        return self.write({"state": "draft"})

    def set_to_draft(self):
        return self.write(
            {
                "state": "draft",
            }
        )

    def set_to_close(self):
        return self.write({"state": "reject"})

    def set_to_close_paid(self):
        return self.write({"state": "reject"})

    def set_to_cancel(self):
        return self.write({"state": "cancel"})

    def create_move(self):
        move_obj = self.env["account.move"]
        for retirement in self:
            if retirement.state == "paid":
                raise ValidationError("Accounting Moves already created.")
            if not retirement.journal_id:
                raise ValidationError("Please specify journal.")
            if not retirement.employee_account:
                raise ValidationError("Please specify employee account.")
            company_currency = retirement.company_id.currency_id
            current_currency = retirement.currency_id
            flag = bool(current_currency and current_currency != company_currency)
            amount = current_currency._convert(
                retirement.amount,
                company_currency,
                retirement.company_id,
                retirement.date,
            )
            asset_name = retirement.name
            reference = retirement.name
            journal_id = retirement.journal_id.id
            if not retirement.employee_id.address_home_id:
                raise ValidationError(
                    f"There is no home address defined for employee: {retirement.employee_id.name}"
                )
            partner_id = retirement.employee_id.address_home_id.id
            if not partner_id:
                raise ValidationError(
                    f"There is no Home address defined for employee: {retirement.employee_id.name}"
                )
            total_amount = sum(l.total_amount for l in retirement.line_ids)
            t1 = current_currency._convert(
                total_amount, company_currency, retirement.company_id, retirement.date
            )
            dr_line = []
            for l in retirement.line_ids:
                amount1 = current_currency._convert(
                    l.total_amount,
                    company_currency,
                    retirement.company_id,
                    retirement.date,
                )
                dr_line.append(
                    (
                        0,
                        0,
                        {
                            "name": asset_name,
                            "ref": reference,
                            "account_id": l.account_id.id,
                            "debit": amount1,
                            "credit": 0.0,
                            "journal_id": journal_id,
                            "partner_id": partner_id,
                            "currency_id": (
                                current_currency.id if flag else company_currency.id
                            ),
                            "date": retirement.date,
                        },
                    )
                )
            cr_line = [
                (
                    0,
                    0,
                    {
                        "name": asset_name,
                        "ref": reference,
                        "account_id": retirement.employee_account.id,
                        "debit": 0.0,
                        "credit": t1,
                        "journal_id": journal_id,
                        "partner_id": partner_id,
                        "currency_id": (
                            current_currency.id if flag else company_currency.id
                        ),
                        "date": retirement.date,
                    },
                )
            ]
            final_list = cr_line + dr_line
            move_vals = {
                "date": retirement.date,
                "ref": reference,
                "journal_id": retirement.journal_id.id,
                "line_ids": final_list,
            }
            move_id = move_obj.create(move_vals)
            retirement.write({"move_id1": move_id.id})
            retirement.employee_id.write(
                {"balance": retirement.employee_id.balance - amount}
            )
            for x in retirement.rec_line_ids:
                if x.allocate_amount > 0.0 and x.ret_id and x.ret_id.move_id1:
                    for j in x.ret_id.move_id1.line_ids:
                        if j.account_id.reconcile:
                            if current_currency != company_currency:
                                p = current_currency._convert(
                                    x.allocate_amount,
                                    company_currency,
                                    retirement.company_id,
                                    retirement.date,
                                )
                            else:
                                p = x.allocate_amount
                            y = x.ret_id.ret_amount + p
                            x.ret_id.write({"ret_amount": y})
                            if y == x.ret_id.amount_total:
                                x.ret_id.write({"state": "rem"})
            retirement.write({"state": "paid"})
        return True

    @api.depends("line_ids")
    def _amount(self):
        self._cr.execute(
            "SELECT s.id,COALESCE(SUM(l.unit_amount*l.unit_quantity),0) AS amount FROM ret_expense s LEFT OUTER JOIN ret_expense_line l ON (s.id=l.expense_id) WHERE s.id IN %s GROUP BY s.id ",
            (tuple(self.ids),),
        )
        res = self._cr.fetchone()
        if res:
            self.amount = res[1]

    @api.model
    def _default_currency_id(self):
        if self.env.user.company_id:
            return self.env.user.company_id.currency_id
        else:
            return self.env["res.currency"].search([("rate", "=", 1.0)], limit=1)

    def _default_employee(self):
        ids = self.env["hr.employee"].search([("user_id", "=", self.env.user.id)])
        if ids:
            return ids[0]
        return False

    @api.model
    def _default_journal(self):
        return (
            self.env.user.company_id
            and self.env.user.company_id.ret_employee_journal
            and self.env.user.company_id.ret_employee_journal
        )

    @api.model
    def _default_account(self):
        return (
            self.env.user.company_id
            and self.env.user.company_id.ret_employee_account
            and self.env.user.company_id.ret_employee_account
        )

    name = fields.Char(string="Name", required=True, readonly=False)
    id = fields.Integer(string="Sheet ID", readonly=False)
    ref = fields.Char(string="Reference", readonly=False)
    date = fields.Date(string="Date", readonly=False, default=fields.Date.today())
    journal_id = fields.Many2one(
        "account.journal",
        string="Journal",
        help="The journal used when accounting for expense.",
        default=_default_journal,
        readonly=False,
    )
    employee_id = fields.Many2one(
        "hr.employee",
        string="Employee",
        required=True,
        readonly=True,
        default=_default_employee,
    )
    user_id = fields.Many2one(
        "res.users", "User", required=True, default=lambda self: self.env.user
    )
    date_confirm = fields.Date(
        string="Confirmation Date",
        help="Date of the confirmation of the sheet expense. It's filled when the button Confirm is pressed.",
        copy=False,
    )
    date_valid = fields.Date(
        string="Validation Date",
        help="Date of the acceptation of the sheet expense. It's filled when the button Accept is pressed.",
        copy=False,
    )
    user_valid = fields.Many2one("res.users", string="Validation User", copy=False)
    account_move_id = fields.Many2one("account.move", string="Ledger Posting")
    line_ids = fields.One2many("ret.expense.line", "expense_id", string="Expense Lines")
    note = fields.Text(
        string="Note",
        readonly=False,
        # states={"paid": [("readonly", True)]}
    )
    amount = fields.Float(compute="_amount", string="Total Amount", store=True)
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        required=True,
        readonly=False,
        default=_default_currency_id,
    )
    department_id = fields.Many2one("hr.department", string="Department")
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        default=lambda self: self.env["res.company"]._company_default_get(
            "hr.employee"
        ),
    )
    state = fields.Selection(
        selection=[
            ("draft", "New"),
            ("open", "Confirmed"),
            ("approve", "Approved"),
            ("paid", "Done"),
            ("rem", "Reimbursed"),
            ("reject", "Rejected"),
            ("cancel", "Cancelled"),
        ],
        string="State",
        required=True,
        default="draft",
        help="When an Retirement is created, the state is 'New'.\n"
        "If the Retirement is confirmed, the state goes in 'Confirmed' \n"
        "If the Retirement is approved, the state goes in 'Approved' \n"
        "If the Retirement's journal entry created, the state goes in 'Done' \n"
        "If the Retirement's reimbursed, the state goes in 'Reimbursed' \n"
        "If the Retirement is rejected, the state goes in 'Rejected' \n"
        "If the Retirement is cancelled, the state goes in 'Cancelled' \n",
        readonly=True,
    )

    move_id1 = fields.Many2one("account.move", string="Journal Entry", copy=False)
    employee_account = fields.Many2one(
        "account.account", string="Employee Account", default=_default_account
    )
    rec_line_ids = fields.One2many(
        "ret.expense.reconcile",
        "ref_id",
        string="Retirement Expense Lines (Reconcile)",
        readonly=False,
    )

    @api.depends("line_ids")
    def _amount(self):
        self._cr.execute(
            """
            SELECT s.id, COALESCE(SUM(l.unit_amount*l.unit_quantity),0) AS amount
            FROM ret_expense s
            LEFT OUTER JOIN ret_expense_line l ON (s.id=l.expense_id)
            WHERE s.id IN %s GROUP BY s.id""",
            (tuple(self.ids),),
        )
        res = self._cr.fetchone()
        if res:
            self.amount = res[1]

    def onchange_employee_id(self, employee_id, currency_id=False, date=False):
        emp_obj = self.env["hr.employee"]
        currecy_obj = self.env["res.currency"]
        department_id = False
        company_id = False
        if employee_id:
            employee = emp_obj.browse(employee_id)
            department_id = employee.department_id.id
            company_id = employee.company_id.id
            adv = []
            adv_ids = self.env["cash.advance"].search(
                [("emp_id", "=", employee_id), ("state", "=", "paid")]
            )
            company_currency = employee.company_id.currency_id
            current_currency = currecy_obj.browse(currency_id)

            ctx = dict(self._context or {})
            ctx.update({"date": date})
            for a in adv_ids:  # sat
                approval_date = False
                if current_currency.id != company_currency.id:
                    org_amount = company_currency.with_context(ctx).compute(
                        a.amount_total, current_currency
                    )
                    open_amount = company_currency.with_context(ctx).compute(
                        a.amount_open, current_currency
                    )
                else:
                    org_amount = a.amount_total
                    open_amount = a.amount_open
                    approval_date = a.approval_date
                r = {
                    "ret_id": a.id,
                    "org_amount": org_amount,
                    "open_amount": open_amount,
                    "approval_date": approval_date,
                }
                adv.append(r)
            if adv_ids:
                return {
                    "value": {
                        "department_id": department_id,
                        "company_id": company_id,
                        "rec_line_ids": adv,
                    }
                }
        return {"value": {"department_id": department_id, "company_id": company_id}}


class HrExpenseRetReconcile(models.Model):
    _name = "ret.expense.reconcile"
    _description = "Retirements Expense Reconcile"
    _order = "approval_date desc"

    def _valid_field_parameter(self, field, name):
        return name == "ondelete" or super()._valid_field_parameter(field, name)

    @api.depends("ret_id")
    def compute_ret_id(self):
        for content in self:
            if content.ret_id:
                content.org_amount = content.ret_id.advance
                content.approval_date = content.ret_id.date
                content.open_amount = content.ret_id.amount_open
            else:
                content.org_amount = content.ret_id.advance
                content.approval_date = content.ret_id.date
                content.open_amount = content.ret_id.amount_open

    ret_id = fields.Many2one(
        "cash.advance",
        string="Expense Advance",
        ondelete="cascade",
        index=True,
        domain=[("state", "=", "paid")],
    )
    ref_id = fields.Many2one("ret.expense", string="Expense Retirement", index=True)
    org_amount = fields.Float(
        string="Advance Amount", digits="Account", compute=compute_ret_id
    )
    open_amount = fields.Float(
        string="Open Balance", digits="Account", compute=compute_ret_id
    )
    allocate_amount = fields.Float(string="Allocation", digits="Account")
    approval_date = fields.Date(
        string="Advance Date", store=True, compute=compute_ret_id
    )
    state = fields.Selection(
        related="ref_id.state"
    )


class HrExpenseLineRet(models.Model):
    _name = "ret.expense.line"
    _description = "Retirement Expense Line"
    _inherit = ["mail.thread"]
    _order = "sequence, date_value desc"

    def _valid_field_parameter(self, field, name):
        return name == "ondelete" or super()._valid_field_parameter(field, name)

    @api.depends("unit_amount", "unit_quantity")
    def _amount(self):
        for con in self:
            con.total_amount = con.unit_quantity * con.unit_amount

    @api.constrains("account_id")
    def _check_accounts(self):
        accounts_c = []
        accounts_e = []
        if self.expense_id.employee_id:
            emp = self.expense_id.employee_id
            for c in emp.category_ids:
                if c.account_ids:
                    accounts_c += map(lambda x: x.id, c.account_ids)
            if emp.account_ids:
                accounts_e = map(lambda x: x.id, emp.account_ids)
            if self.account_id.id in accounts_c:
                return True
            elif self.account_id.id in accounts_e:
                return True
            else:
                raise ValidationError(
                    "It seems you have selected the account which you are not allowed "
                    "to fill/request the retirments of expense"
                )
        return True

    name = fields.Char(string="Expense Note", required=True)
    date_value = fields.Date(string="Date", required=True, default=date.today())
    expense_id = fields.Many2one("ret.expense", string="Expense", ondelete="cascade")
    total_amount = fields.Float(
        compute="_amount", string="Total", digits="Account", store=True
    )
    unit_amount = fields.Float(string="Unit Price")
    unit_quantity = fields.Float(string="Quantities", default=1)
    account_id = fields.Many2one("account.account", string="Account", required=True)
    product_id = fields.Many2one("product.product", string="Product")
    uom_id = fields.Many2one("uom.uom", string="UoM")
    description = fields.Text(string="Description")
    analytic_account = fields.Many2one(
        "account.analytic.account", string="Analytic account"
    )
    ref = fields.Char(string="Reference")
    sequence = fields.Integer(
        string="Sequence",
        help="Gives the sequence order when displaying a list of expense lines.",
    )
    state = fields.Selection(related="expense_id.state")

    def onchange_product_id(self, product_id, uom_id, employee_id):
        res = {}
        if product_id:
            product = self.env["product.product"].browse(product_id)
            res["name"] = product.name
            amount_unit = product.price_get("standard_price")[product.id]
            res["unit_amount"] = amount_unit
            if not uom_id:
                res["uom_id"] = product.uom_id.id
        return {"value": res}

    def onchange_account(self, account_id, employee_id):
        res = {}
        if not account_id:
            return {}
        if not employee_id:
            return {}
        accounts_c = []
        accounts_e = []
        emp = self.env["hr.employee"].browse(employee_id)
        for c in emp.category_ids:
            if c.account_ids:
                accounts_c += map(lambda x: x.id, c.account_ids)
        if emp.account_ids:
            accounts_e = map(lambda x: x.id, emp.account_ids)
        if account_id in accounts_c:
            return {}
        elif account_id in accounts_e:
            return {}
        else:
            return ValidationError(
                "It seems you have selected the account which you are not allowed to fill/request the retirement of expense."
            )
