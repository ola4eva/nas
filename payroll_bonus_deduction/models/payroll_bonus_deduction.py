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
        for vals in vals_list:
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
        return super().create(vals_list)

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

    def _import_find_existing_record(self, vals):
        """Custom method to match on two fields during import."""
        other_input_id = self._resolve_many2one(
            "hr.payslip.input.type", vals.get("other_input_id")
        )
        domain = [
            ("staff_id", "=", vals.get("staff_id")),
            ("other_input_id", "=", other_input_id),
        ]
        return self.search(domain, limit=1)
    
    def _resolve_many2one(self, model, value):
        """Resolve import value to record ID, handling different data types safely."""
        if not value:
            return False
        # If value is an integer, return as is
        if isinstance(value, int):
            return value
        # If value is a string, try external ID or name
        if isinstance(value, str):
            if "." in value:
                record = self.env.ref(value, raise_if_not_found=False)
                if record:
                    return record.id
            # Then, try searching by name
            return self.env[model].search([('name', '=', value)], limit=1).id or False
        # For any other type, return False for safety
        return False

    def _load_records(self, data_list, fields):
        # In Odoo 14, data_list is a list of lists, fields is a list of field names.
        for row in data_list:
            vals = dict(zip(fields, row))
            existing = self._import_find_existing_record(vals)
            if existing:
                if "id" in fields:
                    idx = fields.index("id")
                    row[idx] = existing.id
                else:
                    fields.insert(0, "id")
                    row.insert(0, existing.id)
        return super()._load_records(data_list, fields)
