# -*- coding: utf-8 -*-
from odoo import models, fields
import io
import xlsxwriter
import base64


class PayrollAdviceWizard(models.TransientModel):
    _name = "payroll.advice.wizard"
    _description = "Generate Payroll Advice Spreadsheet"

    file_name = fields.Char(string="File Name")
    file_data = fields.Binary(string="File", readonly=True)

    def generate_payroll_advice(self):
        # Fetch data (Replace this with actual payslip batch query)
        payroll_data = [
            [1, "STAFF001", "John Doe", "GL10", "Bank A", "1234567890", 500000, "HR"],
            [
                2,
                "STAFF002",
                "Jane Smith",
                "GL12",
                "Bank B",
                "0987654321",
                600000,
                "Finance",
            ],
            [
                3,
                "STAFF003",
                "Alice Johnson",
                "GL08",
                "Bank C",
                "1122334455",
                450000,
                "IT",
            ],
            [
                4,
                "STAFF004",
                "Bob Brown",
                "GL11",
                "Bank D",
                "2233445566",
                550000,
                "Admin",
            ],
            [
                5,
                "STAFF005",
                "Charlie White",
                "GL09",
                "Bank E",
                "3344556677",
                470000,
                "Marketing",
            ],
            [
                6,
                "STAFF006",
                "David Black",
                "GL07",
                "Bank F",
                "4455667788",
                400000,
                "Sales",
            ],
            [
                7,
                "STAFF007",
                "Eve Adams",
                "GL13",
                "Bank G",
                "5566778899",
                650000,
                "Legal",
            ],
            [
                8,
                "STAFF008",
                "Frank Harris",
                "GL06",
                "Bank H",
                "6677889900",
                380000,
                "Support",
            ],
            [
                9,
                "STAFF009",
                "Grace Lee",
                "GL14",
                "Bank I",
                "7788990011",
                700000,
                "Operations",
            ],
            [
                10,
                "STAFF010",
                "Henry Kim",
                "GL05",
                "Bank J",
                "8899001122",
                350000,
                "Logistics",
            ],
        ]

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
        for row, data in enumerate(payroll_data, start=6):
            for col, value in enumerate(data):
                sheet.write(row, col, value)

        workbook.close()

        # Encode file to base64
        file_data = base64.b64encode(output.getvalue())
        output.close()

        # Save and return file
        filename = "Payroll Advice " + self.file_name if self.file_name else "Payroll Advice"
        self.write({"file_name": f"{filename}.xlsx", "file_data": file_data})

        return {
            "type": "ir.actions.act_url",
            "url": f"/web/content/?model=payroll.advice.wizard&id={self.id}&field=file_data&filename_field=file_name&download=true",
            "target": "self",
        }
