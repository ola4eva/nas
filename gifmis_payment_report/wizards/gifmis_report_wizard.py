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
    budget_line = fields.Char(
        "Budget Line", required=True, default="21010101-02601-STATFS01008711"
    )

    def action_generate(self):
        payslips = self.payslip_ids
        if self.department_id:
            payslips = payslips.filtered(
                lambda p: p.employee_id.department_id == self.department_id
            )

        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        bold_format = workbook.add_format({"bold": True})
        num_format = workbook.add_format({"num_format": "#,##0.00"})

        headers = [
            "Employee",
            "Bank Account",
            "Description",
            "Amount",
            "Currency",
            "Budget Line",
            "Is Advance Payment",
        ]

        # Group payslips by employee's institute_id
        payslips_by_institute = {}
        for slip in payslips:
            institute = slip.employee_id.institute_id
            if institute not in payslips_by_institute:
                payslips_by_institute[institute] = []
            payslips_by_institute[institute].append(slip)

        for institute, slips in payslips_by_institute.items():
            sheet_name = institute.name if institute else "No Institute"
            worksheet = workbook.add_worksheet(sheet_name[:31])
            for col, header in enumerate(headers):
                worksheet.write(0, col, header, bold_format)

            for idx, slip in enumerate(slips, start=1):
                emp = slip.employee_id
                worksheet.write(idx, 0, emp.employee_no or "")
                worksheet.write(
                    idx, 1, emp.bank_account_id.acc_number or "", num_format
                )
                worksheet.write(idx, 2, self.name or "")
                worksheet.write(idx, 3, slip.net_wage or 0.0, num_format)
                worksheet.write(idx, 4, "NGN")
                worksheet.write(idx, 5, self.budget_line or "")
                worksheet.write(idx, 6, 0)
                worksheet.write(idx, 7, "")

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
