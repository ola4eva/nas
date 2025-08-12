from odoo import models

class PayrollExcelReport(models.AbstractModel):
    _name = 'report.hr_payroll_excel_report.payroll_excel_report_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, wizard):
        sheet = workbook.add_worksheet('Payroll Report')
        bold = workbook.add_format({'bold': True})

        headers = ['Employee Name', 'Staff ID', 'Net Pay']
        for col, header in enumerate(headers):
            sheet.write(0, col, header, bold)

        domain = [
            ('date_from', '>=', wizard.date_from),
            ('date_to', '<=', wizard.date_to),
            ('state', '=', 'done')
        ]
        payslips = self.env['hr.payslip'].search(domain)

        row = 1
        for slip in payslips:
            sheet.write(row, 0, slip.employee_id.name or '')
            sheet.write(row, 1, slip.employee_id.staff_id or '')
            sheet.write(row, 2, slip.net_wage or slip.net or 0.0)
            row += 1
