# -*- coding: utf-8 -*-
import io
import base64
import calendar
import datetime
import xlsxwriter
from odoo import models, fields

REPORT_HEADERS = [
    "SNO",
    "Staff",
    "First Name",
    "Other Names",
    "Gross Pay",
    "NHIS",
]


class NhisDeductionWizard(models.TransientModel):
    _name = "nhis.deduction.wizard"
    _description = "Generate NHIS Deductions Spreadsheet"

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
        domain = [
            ("date_from", ">=", f"{selected_year}-{selected_month:02d}-01"),
            ("date_to", "<=", f"{selected_year}-{selected_month:02d}-{last_day}"),
            ("employee_id", "in", self.employee_ids.ids),
            ("state", "in", ["done", "draft", "verify", "paid"]),
        ]
        payroll_records = self.env["hr.payslip"].search(domain)
        return payroll_records

    def generate_excel_report(self):
        """Generate excel report."""
        payroll_records = self.get_payroll_records()

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {"in_memory": True})

        # Sheet1 - Pension Report
        sheet = workbook.add_worksheet("Sheet1")

        # Set up formats
        title_format = workbook.add_format(
            {"bold": True, "align": "center", "font_size": 14}
        )
        header_format = workbook.add_format({"bold": True, "align": "center"})
        money_format = workbook.add_format({"num_format": "#,##0.00"})

        # Write headers
        sheet.merge_range(
            "A1:E1",
            "NATIONAL AGENCY FOR SCIENCE AND ENGINEERING INFRASTRUCTURE",
            title_format,
        )
        sheet.merge_range(
            "A3:E3",
            "NHIS DEDUCTION FOR THE MONTH OF {}, {}".format(
                calendar.month_name[int(self.month)], self.year
            ),
            title_format,
        )

        for col, header in enumerate(REPORT_HEADERS):
            sheet.write(4, col, header, header_format)

        static_data = [
            (
                index,
                record.employee_id.staff_id or "",
                record.employee_id.name.split(" ")[0],
                record.employee_id.name.split(" ")[-1],
                record.gross_wage,
                self.get_rule_amount(record, "NHIS"),
            )
            for index, record in enumerate(payroll_records, start=1)
        ]
        print(f"Static Data: {static_data} &&&&&&&&&&&&&&&&&&&&")

        for row, data in enumerate(static_data, start=5):
            sheet.write(row, 0, data[0])  # S/N
            sheet.write(row, 1, data[1])  # Staff No
            sheet.write(row, 2, data[2])  # FIRST NAME
            sheet.write(row, 3, data[3])  # Other names
            sheet.write(row, 4, data[4], money_format)  # Gross Wage
            sheet.write(row, 5, data[5], money_format)  # NHIS

        row += 1
        sheet.write(row, 0, "Total", money_format)  # Blank Column
        sheet.write(row, 4, sum(data[4] for data in static_data), money_format)  # Blank Column
        sheet.write(row, 5, sum(data[5] for data in static_data), money_format)  # Blank Column

        workbook.close()
        output.seek(0)
        attachment = self.env["ir.attachment"].create(
            {
                "name": "Pension_Deduction.xlsx",
                "datas": base64.b64encode(output.read()),
                "res_model": "nhis.deduction.wizard",
                "res_id": self.id,
                "type": "binary",
            }
        )
        return {
            "type": "ir.actions.act_url",
            "url": "/web/content/{}?download=true".format(attachment.id),
            "target": "self",
        }
