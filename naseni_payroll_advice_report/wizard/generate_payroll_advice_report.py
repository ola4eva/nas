# -*- coding: utf-8 -*-
from odoo import models, fields
import io
import xlsxwriter
import base64
from odoo import models, fields, api
import calendar
import datetime

PAYROLL_DATA = [
    [1, "STAFF001", "Clement Utom", "GL10", "Bank A", "1234567890", 500000, "HR"],
    [
        2,
        "STAFF002",
        "Dauda Ibrahim",
        "GL12",
        "Bank B",
        "0987654321",
        600000,
        "Finance",
    ],
    [
        3,
        "STAFF003",
        "Ibrahim Yusuff",
        "GL08",
        "Bank C",
        "1122334455",
        450000,
        "IT",
    ],
    [
        4,
        "STAFF004",
        "Joshua Ofiwe",
        "GL11",
        "Bank D",
        "2233445566",
        550000,
        "Admin",
    ],
    [
        5,
        "STAFF005",
        "Lukman Olawale",
        "GL09",
        "Bank E",
        "3344556677",
        470000,
        "Marketing",
    ],
    [
        6,
        "STAFF006",
        "Olufe Adebusola",
        "GL07",
        "Bank F",
        "4455667788",
        400000,
        "Sales",
    ],
    [
        7,
        "STAFF007",
        "Yakubu Tanko",
        "GL13",
        "Bank G",
        "5566778899",
        650000,
        "Legal",
    ],
]


class GeneratePayrollAdviceReport(models.TransientModel):
    _name = "payroll.advice.generate"
    _description = "Generate Payroll Advice Report"

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

    month = fields.Selection(
        [
            (str(index), month)
            for index, month in enumerate(calendar.month_name)
            if month
        ],
        string="Month",
        required=True,
    )

    employee_ids = fields.Many2many(
        "hr.employee",
        string="Employees",
        default=lambda self: self.env["hr.employee"].search([]),
    )
    file_name = fields.Char(string="File Name")
    file_data = fields.Binary(string="File", readonly=True)

    def generate_payroll_advice(self):
        # Fetch data (Replace this with actual payslip batch query)

        # Create an in-memory Excel file
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        sheet = workbook.add_worksheet("Payroll Advice")

        # Add header information before the table
        sheet.merge_range(
            "A1:H1", "NATIONAL AGENCY FOR SCIENCE AND ENGINEERING INFRASTRUCTURE"
        )
        sheet.merge_range("A2:H2", "IDU INDUSTRIAL LAYOUT, ABUJA")
        sheet.merge_range("A3:H3", "PAYROLL DETAIL REPORT FOR POWER EQUIPMENT AND ...")

        # Write headers
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

        # Write data
        
        for row, data in enumerate(PAYROLL_DATA, start=6):
            for col, value in enumerate(data):
                sheet.write(row, col, value)

        workbook.close()

        # Encode file to base64
        file_data = base64.b64encode(output.getvalue())
        output.close()

        # Save and return file
        filename = (
            "Payroll Advice " + self.file_name if self.file_name else "Payroll Advice"
        )
        self.write({"file_name": f"{filename}.xlsx", "file_data": file_data})

        return {
            "type": "ir.actions.act_url",
            "url": f"/web/content/?model=payroll.advice.generate&id={self.id}&field=file_data&filename_field=file_name&download=true",
            "target": "self",
        }
