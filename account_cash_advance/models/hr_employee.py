from odoo import models, fields


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Expense Limit Currency",
    )
    salary_advance_current = fields.Float(string="Salary Advance Current", store=True)
