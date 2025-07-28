from odoo import models, fields

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    staff_id = fields.Char(string='Staff ID', related='employee_id.staff_id', store=True, readonly=True)
