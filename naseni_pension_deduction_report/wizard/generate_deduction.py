# -*- coding: utf-8 -*-
import io
import base64
import calendar
import datetime
import xlsxwriter
from odoo import models, fields
from ..constants import PFA_HEADERS, SUMMARY_HEADERS


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
        domain = [
            ("date_from", ">=", "{}-{:02d}-01".format(selected_year, selected_month)),
            (
                "date_to",
                "<=",
                "{}-{:02d}-{}".format(selected_year, selected_month, last_day),
            ),
            ("employee_id", "in", self.employee_ids.ids),
            ("state", "in", ["done", "verify", "draft", "paid"]),
        ]
        payroll_records = self.env["hr.payslip"].search(domain)
        return payroll_records

    def _get_report_data(self):
        """Prepare data for populating the Excel sheet.

        The returned data structure is organized by PFA (Pension Fund Administrator)
        and includes detailed information for each employee, as well as a summary.

        Example structure:
        {
            "pfa1": [
                {
                    "SNO": 1,
                    "pin": "xxx",
                    "pfa": "PFA1",
                    "staff": 1000,
                    "surname": 100,
                    "other_names": 100,
                    "grosspay": 100,
                    "employee_contr": 100,
                    "employer_contr": 100,
                    "total": 200,
                }
            ],
            "pfa2": [
                {
                    "SNO": 2,
                    "pin": "yyy",
                    "pfa": "PFA2",
                    "staff": 2000,
                    "surname": 200,
                    "other_names": 200,
                    "grosspay": 200,
                    "employee_contr": 200,
                    "employer_contr": 200,
                    "total": 400,
                }
            ],
            "summary": {
                "pfa1": {
                    "grosspay": 1000,
                    "vol_cont": 100,
                    "employee_contr": 100,
                    "employer_contr": 100,
                    "total": 200,
                },
                "pfa2": {
                    "grosspay": 2000,
                    "vol_cont": 200,
                    "employee_contr": 200,
                    "employer_contr": 200,
                    "total": 400,
                },
            },
        }
        """
        data_struct = {}
        payslips = self.get_payroll_records()
        for payslip in payslips:
            employee = payslip.employee_id
            pfa = employee.pfa_id.name if employee.pfa_id else "N/A"
            if pfa not in data_struct:
                data_struct[pfa] = []
            data_struct[pfa].append(
                {
                    "pin": employee.pension_pin or "",
                    "pfa": pfa,
                    "staff": payslip.gross_wage,
                    "surname": employee.name.split(" ")[-1],
                    "other_names": " ".join(employee.name.split(" ")[:-1]),
                    "grosspay": self.get_rule_amount(payslip, "GROSS"),
                    "vol_cont": self.get_rule_amount(payslip, "PENSION_EMPLOYEE"),
                    "employee_contr": self.get_rule_amount(payslip, "PENSION_EMPLOYEE"),
                    "employer_contr": self.get_rule_amount(payslip, "PEN_EMPLOYER"),
                    "total": "xxxx" # Confirm the value that is expected here.
                    + self.get_rule_amount(payslip, "PENSION_EMPLOYER"),
                }
            )
            data_struct["summary"] = {
                "pfa": pfa,
                "grosspay": sum(item["grosspay"] for item in data_struct[pfa]),
                "vol_cont": sum(item["vol_cont"] for item in data_struct[pfa]),
                "employee_contr": sum(item["employee_contr"] for item in data_struct[pfa]),
                "employer_contr": sum(item["employer_contr"] for item in data_struct[pfa]),
                "total": sum(item["total"] for item in data_struct[pfa]),
            }
        return data_struct

    def generate_excel_report(self):
        """Generate excel report."""

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {"in_memory": True})
        # Set up formats
        title_format = workbook.add_format(
            {"bold": True, "align": "center", "font_size": 14}
        )
        header_format = workbook.add_format({"bold": True, "align": "center"})
        money_format = workbook.add_format({"num_format": "#,##0.00"})
        report_data = self._get_report_data()

        for pfa, records in report_data.items():
            # Add headers for each PFA sheet
            sheet = workbook.add_worksheet(pfa)
            sheet.merge_range(
                "A1:E1",
                "NATIONAL AGENCY FOR SCIENCE AND ENGINEERING INFRASTRUCTURE",
                title_format,
            )
            sheet.merge_range(
                "A3:E3",
                "PAYROLL PENSION PAYMENTS FOR THE MONTH OF {}, {}".format(
                    calendar.month_name[int(self.month)], self.year
                ),
                title_format,
            )
            if pfa == "summary":
                for col, header in enumerate(SUMMARY_HEADERS):
                    sheet.write(7, col, header, header_format)
                for row, data in enumerate(records, start=8):
                    sheet.write(row, 0, data["SNO"])
                    sheet.write(row, 1, data["pfa"])
                    sheet.write(row, 2, data["grosspay"])
                    sheet.write(row, 3, data["vol_cont"])
                    sheet.write(row, 4, data["employee_contr"])
                    sheet.write(row, 5, data["employer_contr"], money_format)
                    sheet.write(row, 6, data["total"], money_format)
            else:
                for col, header in enumerate(PFA_HEADERS):
                    sheet.write(7, col, header, header_format)
                for row, data in enumerate(records, start=8):
                    sheet.write(row, 0, data["SNO"])
                    sheet.write(row, 1, data["pin"])
                    sheet.write(row, 2, data["staff"])
                    sheet.write(row, 3, data["surname"])
                    sheet.write(row, 4, data["other_names"])
                    sheet.write(row, 5, data["grosspay"], money_format)
                    sheet.write(row, 6, data["vol_cont"], money_format)
                    sheet.write(row, 7, data["employee_contr"], money_format)
                    sheet.write(row, 8, data["employer_contr"], money_format)
                    sheet.write(row, 9, data["total"], money_format)

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
            "url": "/web/content/{}?download=true".format(attachment.id),
            "target": "self",
        }
