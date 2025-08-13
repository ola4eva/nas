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
    date = fields.Date(string="Date", default=fields.Date.context_today, required=True)
    other_input_id = fields.Many2one(
        "hr.payslip.input.type", string="Other Input", required=True
    )
    amount = fields.Float("Amount", default=0.0)
    state = fields.Selection(
        [("draft", "New"), ("confirm", "Confirmed")],
        string="State",
        default="draft",
        readonly=True,
        tracking=True,
    )
    active = fields.Boolean(string="Active?", default=True)

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
        # Prepare to collect new vals and update existing records
        new_vals_list = []
        for vals in vals_list:
            # Try to find existing record using import logic
            existing = self._import_find_existing_record(vals)
            if existing:
                # Update the existing record with new values
                existing.write(vals)
                continue
            # If no existing record, resolve employee_id if needed
            if "employee_id" not in vals and "staff_id" in vals:
                staff_id = vals.get("staff_id")
                employee = self.env["hr.employee"].search(
                    ["|", ("employee_no", "=", staff_id), ("staff_id", "=", staff_id)],
                    limit=1,
                )
                if employee:
                    vals["employee_id"] = employee.id
                else:
                    vals["employee_id"] = False
            new_vals_list.append(vals)
        if new_vals_list:
            return super().create(new_vals_list)
        else:
            return self.browse()

    @api.onchange("staff_id")
    def _onchange_staff_id(self):
        print("method _onchange_staff_id called")
        if self.staff_id:
            employee = self.env["hr.employee"].search(
                [
                    "|",
                    ("employee_no", "=", self.staff_id),
                    ("staff_id", "=", self.staff_id),
                ],
                limit=1,
            )
            print(f"Found employee: {employee.name if employee else 'None'}")
            if employee:
                self.employee_id = employee.id
            else:
                self.employee_id = False
