# -*- coding: utf-8 -*-
from odoo import models, fields
import io
import xlsxwriter
import base64
from datetime import datetime


class PayrollAdviceWizard(models.TransientModel):
    _name = "pension.deduction.wizard"
    _description = "Generate Pension Deduction Spreadsheet"

    file_name = fields.Char(string="File Name")
    file_data = fields.Binary(string="File", readonly=True)

    def generate_excel_report(self):
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
        sheet1.merge_range(
            "A3:E3",
            f'PENSION DEDUCTION FOR THE MONTH OF {datetime.now().strftime("%B %Y")}',
            title_format,
        )
        headers = [
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
        for col, header in enumerate(headers):
            sheet1.write(4, col, header, header_format)

        # Static data (10 rows)
        static_data = [
            [
                1,  # S/N
                "ABC123",  # Pension Number
                "EMP001",  # Staff No
                "John",  # Surname
                "Doe Bill",  # Other Names
                50000.00,  # Gross Pay
                50000,  # Voluntary Contribution
                12345678,  # Employee Contribution
                50000,  # Employer Contribution
                500000,  # Total
            ],
            [
                2,  # S/N
                "ABC123",  # Pension Number
                "EMP001",  # Staff No
                "Jane",  # Surname
                "Smith Jerome",  # Other Names
                20000.00,  # Gross Pay
                30000,  # Voluntary Contribution
                500000,  # Employee Contribution
                49999,  # Employer Contribution
                89999,  # Total
            ],
            [
                3,  # S/N
                "123GB456",  # Pension Number
                "EMP001",  # Staff No
                "Edinburg",  # Surname
                "Christie M.",  # Other Names
                50000.00,  # Gross Pay
                50000,  # Voluntary Contribution
                12345678,  # Employee Contribution
                50000,  # Employer Contribution
                500000,  # Total
            ],
            [
                4,  # S/N
                "ABC123",  # Pension Number
                "EMP001",  # Staff No
                "John",  # Surname
                "Doe Bill",  # Other Names
                50000.00,  # Gross Pay
                50000,  # Voluntary Contribution
                12345678,  # Employee Contribution
                50000,  # Employer Contribution
                500000,  # Total
            ],
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
        sheet2.write("F6", "Report as at: DD/MM/YY", header_format)
        row = 8

        headers = [
            "S/N",
            "PFA Name",
            "Gross Pay",
            "Voluntary Contribution",
            "Employee Contribution",
            "Employer Contribution",
            "Total",
        ]

        static_data = [
            [1, "Leadway", 700000.00, 10000.00, 700000.00, 899999.000, 680000.00],
            [2, "Leadway", 700000.00, 10000.00, 700000.00, 899999.000, 680000.00],
            [3, "Leadway", 700000.00, 10000.00, 700000.00, 899999.000, 680000.00],
            [4, "Leadway", 700000.00, 10000.00, 700000.00, 899999.000, 680000.00],
            [5, "Leadway", 700000.00, 10000.00, 700000.00, 899999.000, 680000.00],
            [6, "Leadway", 700000.00, 10000.00, 700000.00, 899999.000, 680000.00],
            [7, "Leadway", 700000.00, 10000.00, 700000.00, 899999.000, 680000.00],
            [8, "Leadway", 700000.00, 10000.00, 700000.00, 899999.000, 680000.00],
            [9, "Leadway", 700000.00, 10000.00, 700000.00, 899999.000, 680000.00],
            [10, "Leadway", 700000.00, 10000.00, 700000.00, 899999.000, 680000.00],
        ]

        for col, header in enumerate(headers):
            sheet2.write(7, col, header, header_format)

        # Write the data into the rows
        for row, data in enumerate(static_data, start=8):
            sheet2.write(row, 0, data[0])  # S/N
            sheet2.write(row, 1, data[1])  # PFA Name
            sheet2.write(row, 2, data[2])  # Gross Pay
            sheet2.write(row, 3, data[3])  # Voluntary Contribution
            sheet2.write(row, 4, data[4], money_format)  # Employee Contribution
            sheet2.write(row, 5, data[5], money_format)  # Employer Contribution
            sheet2.write(row, 6, data[6], money_format)  # Total

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

        return {
            "type": "ir.actions.act_url",
            "url": f"/web/content/{attachment.id}?download=true",
            "target": "self",
        }
