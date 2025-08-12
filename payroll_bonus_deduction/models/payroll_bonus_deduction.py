# -*- coding: utf-8 -*-
from datetime import date
from odoo import models, fields, api


class PayrollBonusDeduction(models.Model):
    _name = "payroll.bonus.deduction"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Payroll Bonuses & Deductions"
    _order = "create_date desc"

    name = fields.Char(string="Name", required=True)
    note = fields.Text("Description")
    employee_id = fields.Many2one(
        comodel_name="hr.employee", string="Employee", required=False
    )
    staff_id = fields.Char("Staff ID", required=True)
    date = fields.Date(string="Date", default=date.today(), required=True)
    other_input_id = fields.Many2one(
        "hr.payslip.input.type", string="Other Input", required=True
    )
    amount = fields.Float("Amount", default=0.0)
    state = fields.Selection(
        [("draft", "New"), ("confirm", "Confirmed")],
        string="State",
        default="draft",
        readonly="1",
        tracking=True,
    )
    active = fields.Boolean("Active?", defualt=True)

    def _action_confirm(self):
        return self.write({"state": "confirm"})

    def unlink(self):
        return super(
            PayrollBonusDeduction, self - self.filtered(lambda r: r.state != "draft")
        ).unlink()

    def action_confirm(self):
        """Confirm entries in batch"""
        return (self - self.filtered(lambda r: r.state != "draft"))._action_confirm()

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if "employee_id" not in vals and "staff_id" in vals:
                staff_id = vals.get("staff_id")
                employee = self.env["hr.employee"].search(
                    [("staff_id", "=", staff_id)], limit=1
                )
                if employee:
                    vals["employee_id"] = employee.id
                else:
                    vals["employee_id"] = False
        return super().create(vals_list)

    @api.onchange("staff_id")
    def _onchange_staff_id(self):
        print("method _onchange_staff_id called")
        if self.staff_id:
            employee = self.env["hr.employee"].search(
                [("staff_id", "=", self.staff_id)], limit=1
            )
            print(f"Found employee: {employee.name if employee else 'None'}")
            if employee:
                self.employee_id = employee.id
            else:
                self.employee_id = False
