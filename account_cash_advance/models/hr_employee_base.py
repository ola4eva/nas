import time
from dateutil.relativedelta import relativedelta
from datetime import datetime
from odoo import models, fields, api


class HrEmployeeBase(models.AbstractModel):
    _inherit = "hr.employee.base"

    def _valid_field_parameter(self, field, name):
        return (
            name == "ondelete"
            or name == "ondelete"
            or super()._valid_field_parameter(field, name)
        )

    @api.depends("salary_ids")
    def _get_salary_current_month(self):
        adv = self.env["salary.advance"]
        for emp in self:
            adv_ids = adv.search(
                [
                    ("emp_id", "=", emp.id),
                    ("state", "=", "paid"),
                    (
                        "date",
                        "<=",
                        (
                            datetime.strptime(time.strftime("%Y-%m-%d"), "%Y-%m-%d")
                            + relativedelta(day=31)
                        ).strftime("%Y-%m-%d"),
                    ),
                    (
                        "date",
                        ">=",
                        (
                            datetime.strptime(time.strftime("%Y-%m-%d"), "%Y-%m-%d")
                            - relativedelta(day=1)
                        ).strftime("%Y-%m-%d"),
                    ),
                ]
            )
            for d in adv_ids:
                self.salary_advance_current += d.advance

    salary_ids = fields.One2many(
        "salary.advance",
        "emp_id",
        string="Salary Advances",
        readonly=True,
        ondelete="cascade",
    )
    salary_advance_current = fields.Float(
        compute="_get_salary_current_month",
        string="Current Month Salary Advance",
        store=True,
        help="Show the current month salary advance of employee.",
    )
    salary_advance_policy = fields.Many2many(
        "salary.advance.policy",
        "policy_employee_rel_sadvance",
        "employee_id",
        "policy_id",
        string="Salary Advance Policies",
    )

    account_ids = fields.Many2many(
        "account.account",
        "employee_account_rel",
        "emp_id",
        "account_id",
        string="Account Codes",
    )
    address_home_id = fields.Many2one("res.partner", "Home Address")
    cash_ids = fields.One2many(
        "cash.advance",
        "emp_id",
        string="Cash Advances",
        readonly=True,
        ondelete="cascade",
    )
    limit = fields.Float(
        string="Expense Limit", help="Limit amount of employee for expense advance."
    )
    balance = fields.Float(
        string="Expense Advance Balance",
        readonly=True,
        help="Show the balance of employee for expense advance.",
    )
