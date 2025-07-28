from odoo import http
from odoo.http import request
import io
import xlsxwriter
from datetime import datetime

class PayslipExcelExport(http.Controller):

    @http.route('/export/payslip/excel', type='http', auth='user')
    def export_payslip_excel(self, **kwargs):
        payslip_ids = [int(pid) for pid in kwargs.get('ids', '').split(',') if pid]
        payslips = request.env['hr.payslip'].browse(payslip_ids)

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        sheet = workbook.add_worksheet("Payslips")

        headers = ['Employee', 'Staff ID', 'Date From', 'Date To', 'Net Wage']
        for col, header in enumerate(headers):
            sheet.write(0, col, header)

        for row, payslip in enumerate(payslips, start=1):
            sheet.write(row, 0, payslip.employee_id.name)
            sheet.write(row, 1, payslip.staff_id or '')
            sheet.write(row, 2, payslip.date_from.strftime('%Y-%m-%d'))
            sheet.write(row, 3, payslip.date_to.strftime('%Y-%m-%d'))
            sheet.write(row, 4, payslip.net_wage)

        workbook.close()
        output.seek(0)

        filename = f"Payslips_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        return request.make_response(output.read(), [
            ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
            ('Content-Disposition', f'attachment; filename={filename}')
        ])
