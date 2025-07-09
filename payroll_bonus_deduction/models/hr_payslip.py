import operator
from odoo import models
from odoo.tools import groupby


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'
    
    def compute_sheet(self):
        payslips = self.filtered(lambda slip: slip.state in ["draft", "verify"])
        self.env["hr.payslip.input"].create(payslips._get_other_input_lines())
        super().compute_sheet()

    def _get_other_input_lines(self):
        line_vals = []
        for payslip in self:
            # get other inputs for the payslip related through
            # the employee model
            domain = [
                ('employee_id', '=', payslip.employee_id.id), # employee_id == payslip.employee_id
                ('date', '<=', payslip.date_to), # date is within the month
                ('date', '>=', payslip.date_from), # date is within the month
                ('state', '=', 'confirm'), # state is confirmed
            ]
            employee_other_inputs = self.env['payroll.bonus.deduction'].search(domain).sorted(lambda oi: oi.other_input_id)
            grouped_inputs = groupby(employee_other_inputs, key=operator.itemgetter("other_input_id"))
            for input, deductions in grouped_inputs:
                line_vals.append({
                    "input_type_id": input.id,
                    "name": input.name,
                    "amount": sum([deduction.amount for deduction in deductions]),
                    "payslip_id": payslip.id,
                })
        return line_vals
