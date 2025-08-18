import io
import base64
import calendar
import datetime
import xlsxwriter
from odoo import models, fields


class PayrollSummary(models.Model):
    _name = "payroll.summary.generate"
    _description = "Payroll Summary Wizard"

    file_name = fields.Char()
    file_data = fields.Binary()
    month = fields.Selection(
        [
            (str(index), month)
            for index, month in enumerate(calendar.month_name)
            if month
        ],
        string="Month",
        required=True,
    )
    year = fields.Selection(
        [
            (str(year), str(year))
            for year in range(
                datetime.datetime.now().year - 50, datetime.datetime.now().year + 1
            )
        ],
        string="Year",
        default=str(datetime.datetime.now().year),
        required=True,
    )
    employee_ids = fields.Many2many("hr.employee", string="Employees")

    def generate_payroll_summary(self):
        selected_month = int(self.month)
        selected_year = int(self.year)
        last_day = calendar.monthrange(selected_year, selected_month)[1]

        domain = [
            ("date_from", ">=", f"{selected_year}-{selected_month:02d}-01"),
            ("date_to", "<=", f"{selected_year}-{selected_month:02d}-{last_day}"),
            ("employee_id", "in", self.employee_ids.ids),
            ("state", "in", ["done", "draft", "verify", "paid"]),
        ]
        payslips = self.env["hr.payslip"].search(domain)

        def get_report_data():
            """
            Calculates and returns the structured data for the report.
            This method is called from the wizard.
            """
            self.ensure_one()
            total_amounts = {
                "GROSS_PAY": 0.0,
                "EMPLOYER_PAID_PENSION": 0.0,
                "NHIS": 0.0,
                "NSITF_CONTRIBUTION": 0.0,
                "NET_PAY": 0.0,
                "DEDUCTIONS": {},
            }

            deduction_codes = [
                "AL_HUDA_MPCS",
                "CHILD_SUPPORT_DED",
                "CTLS_SEDI_MINNA",
                "CTLS_ELDI_AWKA",
                "CTLS_JFS",
                "CTLS_PEDI",
                "CTLS_PRODA_ENUGU",
                "CTLS_SEDI_ENUGU",
                "CTLS_SEP_SEDI",
                "CTSS_AMTDI",
                "CTSS_EMDI",
                "CTSS_NEDDI_NNEWI",
                "CTSS_SEDI_DUKIYA",
                "CTSS_SEDI_MINNA",
                "CTSS_SEP_SEDI",
                "CTSS_SSW_SEDI",
                "CTSS_ELDI_AWKA",
                "CTSS_ELDI_WALFARE",
                "CTSS_HEDI_KANO",
                "CTSS_NASENI",
                "CTSS_NEDDI",
                "CTSS_PEDI",
                "CTSS_PEEMADI",
                "CTSS_PRODA_ENUGU",
                "CTSS_SEDI_ENUGU",
                "ERURU_MUSLIM",
                "FGSHLB",
                "FIDEL",
            ]
            for code in deduction_codes:
                total_amounts["DEDUCTIONS"][code] = 0.0

            for slip in payslips:
                for line in slip.line_ids:
                    if line.code in total_amounts:
                        total_amounts[line.code] += line.total
                    elif line.code in total_amounts["DEDUCTIONS"]:
                        total_amounts["DEDUCTIONS"][line.code] += line.total

            total_amounts["TOTAL_PAYOUT"] = (
                total_amounts["GROSS_PAY"]
                + total_amounts["EMPLOYER_PAID_PENSION"]
                + total_amounts["NHIS"]
                + total_amounts["NSITF_CONTRIBUTION"]
            )
            return total_amounts

        report_data = get_report_data()

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {"in_memory": True})
        worksheet = workbook.add_worksheet("Payroll Summary")

        # Add a bold format
        bold = workbook.add_format({"bold": True})

        # Report Title and Header
        worksheet.write(
            "A1", "NATIONAL AGENCY FOR SCIENCE AND ENGINEERING INFRASTRUCTURE", bold
        )
        worksheet.write("A2", "IDU INDUSTRIAL LAYOUT, ABUJA")
        worksheet.write(
            "A4", f"SALARY PAYOUT SUMMARY FOR {self.file_name.replace(" ", "_")}", bold
        )

        # Write the first table
        row = 6
        worksheet.write(row, 0, "PAY ITEM", bold)
        worksheet.write(row, 1, "AMOUNT", bold)
        row += 1

        # Write the data from the report
        worksheet.write(row, 0, "GROSS PAY")
        worksheet.write(row, 1, report_data["GROSS_PAY"])
        row += 1

        worksheet.write(row, 0, "EMPLOYER PAID PENSION")
        worksheet.write(row, 1, report_data["EMPLOYER_PAID_PENSION"])
        row += 1

        worksheet.write(row, 0, "NHIS")
        worksheet.write(row, 1, report_data["NHIS"])
        row += 1

        worksheet.write(row, 0, "NSITF CONTRIBUTION")
        worksheet.write(row, 1, report_data["NSITF_CONTRIBUTION"])
        row += 1

        worksheet.write(row, 0, "TOTAL PAYOUT", bold)
        worksheet.write(row, 1, report_data["TOTAL_PAYOUT"])
        row += 2

        # Write the second table
        worksheet.write(row, 0, "PAY ITEM", bold)
        worksheet.write(row, 1, "AMOUNT", bold)
        row += 1

        worksheet.write(row, 0, "NET PAY", bold)
        worksheet.write(row, 1, report_data["NET_PAY"])
        row += 1

        # Write deductions
        for item, amount in report_data["DEDUCTIONS"].items():
            worksheet.write(row, 0, item.replace("_", " ").title())
            worksheet.write(row, 1, amount)
            row += 1

        workbook.close()
        output.seek(0)

        # Create a transient record to hold the Excel file for download
        excel_file_data = base64.b64encode(output.read())
        excel_name = f"Payroll_Summary_{self.file_name.replace(" ", "_")}.xlsx"

        attachment = self.env["ir.attachment"].create(
            {
                "name": excel_name,
                "datas": excel_file_data,
                "type": "binary",
                "res_model": "naseni.payroll.excel.report.wizard",
                "res_id": self.id,
            }
        )
        return {
            "type": "ir.actions.act_url",
            "url": f"/web/content/{attachment.id}?download=true",
            "target": "new",
        }
