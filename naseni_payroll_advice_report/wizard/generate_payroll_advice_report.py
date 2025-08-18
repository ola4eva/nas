import io
import base64
import xlsxwriter
import calendar
import datetime
from odoo import models, fields
from ..constants import REPORT_HEADERS, TEXT, get_element_value, NUM


class PayrollAdvice(models.Model):
    _name = "payroll.advice.generate"
    _description = "Payroll Advice Wizard"

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

    def generate_payroll_advice(self):
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

        PAYROLL_DATA = []

        for index, rec in enumerate(payslips, start=1):
            PAYROLL_DATA.append(
                (
                    (index, TEXT),
                    (rec.employee_id.employee_no or "N/A", TEXT),
                    (rec.employee_id.name, TEXT),
                    (
                        (rec.employee_id.grade_id.name, TEXT)
                        if rec.employee_id.grade_id
                        else ("N/A", TEXT)
                    ),
                    (
                        (rec.employee_id.institute_id.name, TEXT)
                        if rec.employee_id.institute_id
                        else ("N/A", TEXT)
                    ),
                    (
                        (rec.employee_id.bank_account_id.bank_id.name, TEXT)
                        if rec.employee_id.bank_account_id
                        else ("N/A", TEXT)
                    ),
                    (
                        (rec.employee_id.bank_account_id.acc_number, TEXT)
                        if rec.employee_id.bank_account_id
                        else ("N/A", TEXT)
                    ),
                    *[
                        (get_element_value(rec, header[0]), header[2])
                        for header in REPORT_HEADERS[7:]
                    ],
                )
            )

        # Create Excel file
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        sheet = workbook.add_worksheet("Payroll Advice")
        # Formats
        text_format = workbook.add_format({"align": "left"})
        number_format = workbook.add_format({"num_format": "#,##0.00", "align": "right"})
        header_format = workbook.add_format({"bold": True, "align": "left"})

        def get_format(type=""):
            formats = {
                "number": number_format,
                "text": text_format,
                "header": header_format,
            }
            return formats.get(type, text_format)

        sheet.merge_range(
            "A1:H1",
            "NATIONAL AGENCY FOR SCIENCE AND ENGINEERING INFRASTRUCTURE",
            get_format("header_format"),
        )
        sheet.merge_range(
            "A2:H2", "IDU INDUSTRIAL LAYOUT, ABUJA", get_format("header_format")
        )
        sheet.merge_range(
            "A3:H3",
            f"PAYROLL DETAIL REPORT FOR {calendar.month_name[selected_month]} {selected_year}",
            get_format("header_format"),
        )

        for col, header in enumerate(REPORT_HEADERS):
            sheet.write(5, col, header[1], get_format("header"))

        # Write data
        for row, data in enumerate(PAYROLL_DATA, start=6):
            for col, value in enumerate(data):
                sheet.write(row, col, value[0], get_format(value[1]))

        workbook.close()

        file_data = base64.b64encode(output.getvalue()).decode("utf-8")
        output.close()

        filename = (
            f"Payroll Advice {calendar.month_name[selected_month]} {selected_year}"
        )
        self.write({"file_name": f"{filename}.xlsx", "file_data": file_data})

        return {
            "type": "ir.actions.act_url",
            "url": f"/web/content/?model=payroll.advice.generate&id={self.id}&field=file_data&filename_field=file_name&download=true",
            "target": "self",
        }
