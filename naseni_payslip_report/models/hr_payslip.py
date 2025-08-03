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

    def get_pension(self):
        return self.get_component("PENSION_EMPLOYEE")

    def get_tax(self):
        return self.get_component("PAYE")

    def belongs_to_tsaon(self):
        return self.employee_id.trade_union == "tsaon"

    def belongs_to_nasu(self):
        return self.employee_id.trade_union == "nasu"

    def belongs_to_ssauthriai(self):
        return self.employee_id.trade_union == "ssauthriai"

    def get_tsaon(self):
        return self.get_component("TSAON")

    def get_ssauthriai(self):
        return self.get_component("SSAUTHRIAI")

    def get_nasu(self):
        return self.get_component("NASU")

    def get_ctss_naseni(self):
        return self.get_component("CTSS_NASENI")

    def get_nhf(self):
        return self.get_component("NHF")

    def get_gross(self):
        return self.get_component("GROSS")

    def get_total_deduction(self):
        total_deduction = (
            self.get_tax()
            + self.get_nasu()
            + self.get_tsaon()
            + self.get_ssauthriai()
            + self.get_pension()
            + self.get_nhf()
            + self.get_other_deductions()
        )
        return total_deduction

    def get_net(self):
        return self.get_component("NET")
