# -*- coding: utf-8 -*-
import io
import base64
import calendar
import datetime
import xlsxwriter
from odoo import models, fields

SHEET_ONE_HEADERS = [
    "S/N",
    "Pension Number",
    "Staff No",
    "Surname",
    "Other Names",
    "Gross Pay",
    "Voluntary Contribution",
    "Employee Contribution",
    "Employer Contribution",
    "Total",
]

SHEET_TWO_HEADERS = [
    "S/N",
    "PFA Name",
    "Gross Pay",
    "Voluntary Contribution",
    "Employee Contribution",
    "Employer Contribution",
    "Total",
]


class PayrollAdviceWizard(models.TransientModel):
    _name = "pension.deduction.wizard"
    _description = "Generate Pension Deduction Spreadsheet"

    file_name = fields.Char(string="File Name")
    file_data = fields.Binary(string="File", readonly=True)
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

    def get_rule_amount(self, payroll_record, code):
        """Get salary rule amount based on salary rule"""
        line = payroll_record.line_ids.filtered(
            lambda line: line.salary_rule_id.code == code
        )
        if line:
            return line.total
        return 0.0

    def get_payroll_records(self):
        """Get payroll records"""
        selected_month = int(self.month)
        selected_year = int(self.year)

        # Get last valid day of the month
        last_day = calendar.monthrange(selected_year, selected_month)[1]
        # Fetch payroll data for the selected month, year, and employees
        # domain = [
        #     ("date_from", ">=", f"{selected_year}-{selected_month:02d}-01"),
        #     ("date_to", "<=", f"{selected_year}-{selected_month:02d}-{last_day}"),
        #     ("employee_id", "in", self.employee_ids.ids),
        #     ("state", "in", ["done", "paid"]),  # Only include processed payslips
        # ]
        domain = [
            ("date_from", ">=", "{}-{:02d}-01".format(selected_year, selected_month)),
            ("date_to", "<=", "{}-{:02d}-{}".format(selected_year, selected_month, last_day)),
            ("employee_id", "in", self.employee_ids.ids),
            ("state", "in", ["done", "verify", "draft", "paid"]),  # Only include processed payslips
        ]
        payroll_records = self.env["hr.payslip"].search(domain)
        return payroll_records

    def generate_excel_report(self):
        """Generate excel report."""
        payroll_records = self.get_payroll_records()

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {"in_memory": True})

        # Sheet1 - Pension Report
        sheet1 = workbook.add_worksheet("Sheet1")

        # Set up formats
        title_format = workbook.add_format(
            {"bold": True, "align": "center", "font_size": 14}
        )
        header_format = workbook.add_format({"bold": True, "align": "center"})
        money_format = workbook.add_format({"num_format": "#,##0.00"})

        # Write headers
        sheet1.merge_range(
            "A1:E1",
            "NATIONAL AGENCY FOR SCIENCE AND ENGINEERING INFRASTRUCTURE",
            title_format,
        )
        # sheet1.merge_range(
        #     "A3:E3",
        #     f"PENSION DEDUCTION FOR THE MONTH OF {calendar.month_name[int(self.month)]}, {self.year}",
        #     title_format,
        # )
        sheet1.merge_range(
            "A3:E3",
            "PENSION DEDUCTION FOR THE MONTH OF {}, {}".format(
                calendar.month_name[int(self.month)], self.year
            ),
            title_format,
        )

        for col, header in enumerate(SHEET_ONE_HEADERS):
            sheet1.write(4, col, header, header_format)

        static_data = [
            (
                index,
                record.employee_id.pension_pin or "",
                record.employee_id.employee_no or "",
                record.employee_id.name.split(" ")[0],
                record.employee_id.name.split(" ")[-1],
                record.gross_wage,
                45000,
                self.get_rule_amount(record, "PENSION_EMPLOYEE"),
                self.get_rule_amount(record, "PEN_EMPLOYER"),
                self.get_rule_amount(record, "PENSION_EMPLOYEE")
                + self.get_rule_amount(record, "PEN_EMPLOYER"),
                record.employee_id.pfa_id.name or "",
            )
            for index, record in enumerate(payroll_records, start=1)
        ]

        for row, data in enumerate(static_data, start=5):
            sheet1.write(row, 0, data[0])  # S/N
            sheet1.write(row, 1, data[1])  # Pension No
            sheet1.write(row, 2, data[2])  # Staff No
            sheet1.write(row, 3, data[3])  # Surname
            sheet1.write(row, 4, data[4], money_format)  # Other names
            sheet1.write(row, 5, data[5], money_format)  # Gross Pay
            sheet1.write(row, 6, data[6], money_format)  # Voluntary Contribution
            sheet1.write(row, 7, data[7], money_format)  # Employee Contribution
            sheet1.write(row, 8, data[8], money_format)  # Employer Contribution
            sheet1.write(row, 9, data[9], money_format)  # Total

        # Sheet2 - Summary Report
        sheet2 = workbook.add_worksheet("Sheet2")

        # Write headers for Sheet2
        sheet2.merge_range(
            "B2:G2",
            "NATIONAL AGENCY FOR SCIENCE AND ENGINEERING INFRASTRUCTURE",
            title_format,
        )
        sheet2.merge_range("B4:G4", "PENSION DEDUCTION SUMMARY", title_format)
        # sheet2.write(
        #     "F6",
        #     f"Report as at: {datetime.datetime.now().strftime("%d/%m/%Y")}",
        #     header_format,
        # )
        sheet2.write(
            "F6",
            "Report as at: {}".format(
                datetime.datetime.now().strftime("%d/%m/%Y")
            ),
            header_format,
        )

        row = 7

        for col, header in enumerate(SHEET_TWO_HEADERS):
            sheet2.write(row, col, header, header_format)
        row += 1

        # Write the data into the rows
        for row, data in enumerate(static_data, start=row):
            sheet2.write(row, 0, data[0])  # S/N
            sheet2.write(row, 1, data[10])  # PFA Name
            sheet2.write(row, 2, data[5])  # Gross Pay
            sheet2.write(row, 3, data[6])  # Voluntary Contribution
            sheet2.write(row, 4, data[7], money_format)  # Employee Contribution
            sheet2.write(row, 5, data[8], money_format)  # Employer Contribution
            sheet2.write(row, 6, data[9], money_format)  # Total

        workbook.close()
        output.seek(0)
        attachment = self.env["ir.attachment"].create(
            {
                "name": "Pension_Deduction.xlsx",
                "datas": base64.b64encode(output.read()),
                "res_model": "pension.deduction.wizard",
                "res_id": self.id,
                "type": "binary",
            }
        )

        # return {
        #     "type": "ir.actions.act_url",
        #     "url": f"/web/content/{attachment.id}?download=true",
        #     "target": "self",
        # }
        return {
            "type": "ir.actions.act_url",
            "url": "/web/content/{}?download=true".format(attachment.id),
            "target": "self",
        }
