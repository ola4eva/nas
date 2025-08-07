from odoo import models


class HrPayslip(models.Model):
    _inherit = "hr.payslip"

    def get_component(self, code):
        self.ensure_one()
        return abs(sum((self.line_ids.filtered(lambda l: l.code == code).mapped("total"))))
    
    def get_other_deductions(self):
        return abs(sum(self.line_ids.filtered(lambda l: l.category_id.code == "ODD").mapped("total")))

    def get_basic_salary(self):
        return self.get_component("BASIC")

    def get_gross(self):
        return self.get_component("GROSS")

    def get_total_deduction(self):
        total_deduction = (
            self.get_tax()
            + self.get_nasu()
            + self.get_tsan()
            + self.get_ssauthriai()
            + self.get_pension()
            + self.get_nhf()
            + self.get_other_deductions()
        )
        return total_deduction

    def get_net(self):
        return self.get_component("NET")
