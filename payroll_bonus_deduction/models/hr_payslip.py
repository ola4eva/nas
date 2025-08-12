import operator
from functools import reduce
from odoo import models
from odoo.tools import groupby


class HrPayslip(models.Model):
    _inherit = "hr.payslip"

    def compute_sheet(self):
        payslips = self.filtered(lambda slip: slip.state in ["draft", "verify"])
        # ✅ Delete existing input lines to prevent duplication
        payslips.mapped("input_line_ids").unlink()
        # ✅ Create new input lines for other inputs
        self.env["hr.payslip.input"].create(payslips._get_other_input_lines())
        super().compute_sheet()

    def _get_other_input_lines(self):
        line_vals = []
        for payslip in self:
            # get other inputs for the payslip related through
            # the employee model
            domain = [
                (
                    "employee_id",
                    "=",
                    payslip.employee_id.id,
                ),  # employee_id == payslip.employee_id
                ("state", "=", "confirm"),  # state is confirmed
            ]
            employee_other_inputs = (
                self.env["payroll.bonus.deduction"]
                .search(domain)
                .sorted(lambda oi: oi.other_input_id)
            )
            grouped_inputs = groupby(
                employee_other_inputs, key=operator.itemgetter("other_input_id")
            )
            for input, deductions in grouped_inputs:
                return_most_recent = lambda x, y: (
                    x if x.create_date > y.create_date else y
                )

                line_vals.append(
                    {
                        "input_type_id": input.id,
                        "name": input.name,
                        "amount": list(reduce(return_most_recent, deductions))[
                            0
                        ].amount,
                        "payslip_id": payslip.id,
                    }
                )
        return line_vals
