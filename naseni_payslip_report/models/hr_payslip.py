from odoo import models


class HrPayslip(models.Model):
    _inherit = "hr.payslip"

    def get_component(self, code):
        self.ensure_one()
        return sum(self.line_ids.filtered(lambda l: l.code == code).mapped("total"))

    def get_basic_salary(self):
        return self.get_component("BASIC")

    def get_pension(self):
        return self.get_component("PEN")

    def get_tax(self):
        return self.get_component("TAX")

    def get_tax_arrears(self):
        return self.get_component("TAX_ARREARS")

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
            self.get_tax() +
            self.get_tax_arrears() +
            self.get_nasu() +
            self.get_ctss_naseni() +
            self.get_nhf()
        )
        return total_deduction

    def get_net(self):
        return self.get_component("NET")
