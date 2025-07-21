from odoo import models, fields
from io import BytesIO
import base64
import xlsxwriter


class GifmisReportWizard(models.TransientModel):
    _name = "gifmis.report.wizard"
    _description = "GIFMIS Report Wizard"

    department_id = fields.Many2one("hr.department", string="Department (optional)")
    payslip_ids = fields.Many2many("hr.payslip", string="Payslips")
    name = fields.Char("Description", required=True, default="GIFMIS Payment Upload")

    def action_generate(self):
        payslips = self.payslip_ids
        if self.department_id:
            payslips = payslips.filtered(
                lambda p: p.employee_id.department_id == self.department_id
            )

        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet("GIFMIS Payment Upload")

        headers = [
            "Employee",
            "Bank Account",
            "Description",
            "Amount",
            "Currency",
            "Budget Line",
            "Is Advance",
            "Payment",
        ]

        for col, header in enumerate(headers):
            worksheet.write(0, col, header)

        for idx, slip in enumerate(payslips, start=1):
            emp = slip.employee_id
            worksheet.write_row(
                idx,
                0,
                [
                    emp.staff_id or "",
                    emp.bank_account_id.acc_number or "",
                    self.name or "",
                    slip.net_wage or 0.0,
                    "NGN",
                    "",
                    0,
                    "",
                ],
            )

        workbook.close()
        output.seek(0)

        attachment = self.env["ir.attachment"].create(
            {
                "name": "gifmis_payment_upload.xlsx",
                "type": "binary",
                "datas": base64.b64encode(output.read()),
                "mimetype": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "res_model": "gifmis.report.wizard",
                "res_id": self.id,
            }
        )

        return {
            "type": "ir.actions.act_url",
            "url": f"/web/content/{attachment.id}?download=true",
            "target": "new",
        }
