from odoo import models, fields

class PayrollReportWizard(models.TransientModel):
    _name = 'payroll.report.wizard'
    _description = 'Payroll Report Wizard'

    date_from = fields.Date(string='Date From', required=True)
    date_to = fields.Date(string='Date To', required=True)

    def generate_excel_report(self):
        return self.env.ref('hr_payroll_excel_report.action_payroll_excel_report').report_action(self)
