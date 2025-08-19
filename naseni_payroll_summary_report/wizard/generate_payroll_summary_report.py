import io
import base64
import calendar
import datetime
import xlsxwriter
from odoo import models, fields
from ..constants import DEDUCTION_CODES


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
                "GROSS": 0.0,
                "PEN_EMPLOYER": 0.0,
                "NHIS": 0.0,
                "NSITF": 0.0,
                "NET": 0.0,
                "DEDUCTIONS": {},
            }

            for code in DEDUCTION_CODES:
                total_amounts["DEDUCTIONS"][code[0]] = 0.0

            for slip in payslips:
                for line in slip.line_ids:
                    if line.code in total_amounts:
                        total_amounts[line.code] += line.total
                    if line.code in total_amounts["DEDUCTIONS"]:
                        total_amounts["DEDUCTIONS"][line.code] += line.total

            total_amounts["TOTAL_PAYOUT"] = (
                total_amounts["GROSS"]
                + total_amounts["PEN_EMPLOYER"]
                + total_amounts["NHIS"]
                + total_amounts["NSITF"]
            )
            return total_amounts

        report_data = get_report_data()

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {"in_memory": True})
        worksheet = workbook.add_worksheet("Payroll Summary")

        # Add a bold format
        bold = workbook.add_format({"bold": True})
        number_format = workbook.add_format({"num_format": "#,##0.00"})
        bold_number_format = workbook.add_format(
            {"bold": True, "num_format": "#,##0.00"}
        )
        border_format = workbook.add_format({"border": 1})
        merge_format = workbook.add_format(
            {
                "bold": 1,
                "border": 1,
                "align": "center",
                "valign": "vcenter",
            }
        )

        # Report Title and Header
        worksheet.merge_range(
            "B2:C2",
            "NATIONAL AGENCY FOR SCIENCE AND ENGINEERING INFRASTRUCTURE",
            merge_format,
        )
        worksheet.merge_range("B3:C3", "IDU INDUSTRIAL LAYOUT, ABUJA", merge_format)
        worksheet.merge_range(
            "B5:C5",
            f"SALARY PAYOUT SUMMARY FOR {(calendar.month_name[int(self.month)]).upper()} {self.year}",
            merge_format,
        )

        row = 5
        worksheet.write(row, 1, "PAY ITEM", bold)
        worksheet.write(row, 2, "AMOUNT", bold)
        row += 1

        # Write the data from the report
        worksheet.write(row, 1, "GROSS PAY")
        worksheet.write(row, 2, report_data["GROSS"], number_format)
        row += 1

        worksheet.write(row, 1, "EMPLOYER PAID PENSION")
        worksheet.write(row, 2, report_data["PEN_EMPLOYER"], number_format)
        row += 1

        worksheet.write(row, 1, "NHIS")
        worksheet.write(row, 2, report_data["NHIS"], number_format)
        row += 1

        worksheet.write(row, 1, "NSITF CONTRIBUTION")
        worksheet.write(row, 2, report_data["NSITF"], number_format)
        row += 1

        worksheet.write(row, 1, "TOTAL PAYOUT", bold)
        worksheet.write(row, 2, report_data["TOTAL_PAYOUT"], number_format)
        row += 2

        # Write the second table
        worksheet.write(row, 1, "PAY ITEM", bold)
        worksheet.write(row, 2, "AMOUNT", bold)
        row += 1

        worksheet.write(row, 1, "NET PAY")
        worksheet.write(row, 2, report_data["NET"], number_format)
        row += 1

        col = 1
        # Write deductions
        for item, amount in report_data["DEDUCTIONS"].items():
            worksheet.write(row, col, item)
            worksheet.write(row, col + 1, amount, number_format)
            row += 1

        worksheet.write(row, col, "TOTAL PAYOUT", bold)
        worksheet.write(row, col + 1, report_data["TOTAL_PAYOUT"], bold_number_format)

        # Add conditional formatting for borders in B1:C61
        worksheet.conditional_format(
            "B2:C62", {"type": "no_blanks", "format": border_format}
        )
        # worksheet.conditional_format("B2:C62", {"type": "blanks", "format": border_format})

        workbook.close()
        output.seek(0)

        # Create a transient record to hold the Excel file for download
        excel_file_data = base64.b64encode(output.read())
        excel_name = f"Payroll_Summary_{self.file_name.replace(' ', '_')}.xlsx"

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
