from odoo import models, fields


class HrEmployeeCategory(models.Model):
    _inherit = "hr.employee.category"
    _description = "Employee Category"

    salary_advance_policy = fields.Many2many(
        "salary.advance.policy",
        "employee_category_policy_rel_sadvance",
        "category_id",
        "policy_id",
        string="Salary Advance Policies",
    )
    # account_ids = fields.Many2many(
    #     "account.account",
    #     "employee_category_account_rel",
    #     "category_id",
    #     "account_id",
    #     string="Account Codes",
    # )
