import io
import base64
import xlsxwriter
import calendar
import datetime
from odoo import models, fields


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
        # Convert month from selection (str index) to actual integer
        selected_month = int(self.month)
        selected_year = int(self.year)

        # Get last valid day of the month
        last_day = calendar.monthrange(selected_year, selected_month)[1]

        # Fetch payroll data for the selected month, year, and employees
        domain = [
            ("date_from", ">=", f"{selected_year}-{selected_month:02d}-01"),
            ("date_to", "<=", f"{selected_year}-{selected_month:02d}-{last_day}"),
            ("employee_id", "in", self.employee_ids.ids),
            ("state", "in", ["done", "paid"]),  # Only include processed payslips
        ]
        payroll_records = self.env["hr.payslip"].search(domain)

        PAYROLL_DATA = [
            (
                index,
                rec.employee_id.staff_id or "N/A",
                rec.employee_id.name,
                rec.employee_id.grade_id.name if rec.employee_id.grade_id else "N/A",
                rec.employee_id.bank_account_id.bank_id.name if rec.employee_id.bank_account_id else "N/A",
                (
                    rec.employee_id.bank_account_id.acc_number
                    if rec.employee_id.bank_account_id
                    else "N/A"
                ),
                rec.net_wage,
                rec.department_id.name if rec.department_id else "N/A",
            )
            for index, rec in enumerate(payroll_records, start=1)
        ]

        # Create an in-memory Excel file
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        sheet = workbook.add_worksheet("Payroll Advice")

        # Add header information
        sheet.merge_range(
            "A1:H1", "NATIONAL AGENCY FOR SCIENCE AND ENGINEERING INFRASTRUCTURE"
        )
        sheet.merge_range("A2:H2", "IDU INDUSTRIAL LAYOUT, ABUJA")
        sheet.merge_range(
            "A3:H3",
            f"PAYROLL DETAIL REPORT FOR {calendar.month_name[selected_month]} {selected_year}",
        )

        # Write table headers
        headers = [
            "SNO",
            "STAFF ID",
            "STAFF NAME",
            "GRADELEVEL",
            "BANK",
            "ACC NO",
            "Net Pay",
            "CENTRE",
        ]
        for col, header in enumerate(headers):
            sheet.write(5, col, header)

        # Write payroll data
        for row, data in enumerate(PAYROLL_DATA, start=6):
            for col, value in enumerate(data):
                sheet.write(row, col, value)

        workbook.close()

        # Encode file to base64
        file_data = base64.b64encode(output.getvalue()).decode("utf-8")
        output.close()

        # Save and return file
        filename = (
            f"Payroll Advice {calendar.month_name[selected_month]} {selected_year}"
        )
        self.write({"file_name": f"{filename}.xlsx", "file_data": file_data})

        return {
            "type": "ir.actions.act_url",
            "url": f"/web/content/?model=payroll.advice.generate&id={self.id}&field=file_data&filename_field=file_name&download=true",
            "target": "self",
        }
