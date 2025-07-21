from odoo import models, fields
from io import BytesIO
import base64
import xlsxwriter

class GifmisReportWizard(models.TransientModel):
    _name = 'gifmis.report.wizard'
    _description = 'GIFMIS Report Wizard'

    department_id = fields.Many2one('hr.department', string='Department (optional)')
    payslip_ids = fields.Many2many('hr.payslip', string='Payslips')

    def action_generate(self):
        payslips = self.payslip_ids
        if self.department_id:
            payslips = payslips.filtered(lambda p: p.employee_id.department_id == self.department_id)

        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet('GIFMIS Payment Upload')

        headers = [
            'S/N', 'Personnel Number', 'IPPIS NO', 'Surname', 'First Name',
            'Middle Name', 'Account Number', 'Bank Name', 'Bank Code',
            'Amount', 'Remark'
        ]

        for col, header in enumerate(headers):
            worksheet.write(0, col, header)

        for idx, slip in enumerate(payslips, start=1):
            emp = slip.employee_id
            name_parts = emp.name.split(' ') if emp.name else []
            worksheet.write_row(idx, 0, [
                idx,
                emp.staff_id or '',
                emp.ippis_no or '',
                name_parts[0] if len(name_parts) > 0 else '',
                name_parts[1] if len(name_parts) > 1 else '',
                name_parts[2] if len(name_parts) > 2 else '',
                emp.bank_account_id.acc_number or '',
                emp.bank_account_id.bank_id.name or '',
                emp.bank_account_id.bank_id.bic or '',
                slip.net_wage or 0.0,
                ''
            ])

        workbook.close()
        output.seek(0)

        attachment = self.env['ir.attachment'].create({
            'name': 'gifmis_payment_upload.xlsx',
            'type': 'binary',
            'datas': base64.b64encode(output.read()),
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'res_model': 'gifmis.report.wizard',
            'res_id': self.id,
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'new',
        }
