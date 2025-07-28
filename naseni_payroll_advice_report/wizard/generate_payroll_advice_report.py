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
        selected_month = int(self.month)
        selected_year = int(self.year)
        last_day = calendar.monthrange(selected_year, selected_month)[1]

        domain = [
            ("date_from", ">=", f"{selected_year}-{selected_month:02d}-01"),
            ("date_to", "<=", f"{selected_year}-{selected_month:02d}-{last_day}"),
            ("employee_id", "in", self.employee_ids.ids),
            ("state", "in", ["done", "paid"]),
        ]
        payroll_records = self.env["hr.payslip"].search(domain)

        PAYROLL_DATA = []

        for index, rec in enumerate(payroll_records, start=1):
            # Input types
            SWIS_MPCS_PEEMADI = 0.0
            AL_HUDA_MPCS = 0.0
            CTSS_NASENI = 0.0
            CTSS_PEEMADI = 0.0
            FMBN_RENOVATION = 0.0
            NASENI_CSL = 0.0
            FIDELITY_DEBT = 0.0

            # Salary rules
            basic = 0.0
            gross = 0.0
            NHF = 0.0
            TSAN = 0.0
            NASU = 0.0
            SSAUTHRIAI = 0.0

            for input_line in rec.input_line_ids:
                if input_line.code == "SWIS_MPCS_PEEMADI":
                    SWIS_MPCS_PEEMADI = input_line.amount
                elif input_line.code == "AL_HUDA_MPCS":
                    AL_HUDA_MPCS = input_line.amount
                elif input_line.code == "CTSS_NASENI":
                    CTSS_NASENI = input_line.amount
                elif input_line.code == "CTSS_PEEMADI":
                    CTSS_PEEMADI = input_line.amount
                elif input_line.code == "FMBN_RENOVATION":
                    FMBN_RENOVATION = input_line.amount
                elif input_line.code == "NASENI_CSL":
                    NASENI_CSL = input_line.amount
                elif input_line.code == "FIDELITY_DEBT":
                    FIDELITY_DEBT = input_line.amount

            for line in rec.line_ids:
                if line.code == "BASIC":
                    basic = line.total
                elif line.code == "GROSS":
                    gross = line.total
                elif line.code == "NHF":
                    NHF = line.total
                elif line.code == "TSAN":
                    TSAN = line.total
                elif line.code == "NASU":
                    NASU = line.total
                elif line.code == "SSAUTHRIAI":
                    SSAUTHRIAI = line.total


            PAYROLL_DATA.append((
                index,
                rec.employee_id.staff_id or "N/A",
                rec.employee_id.name,
                rec.employee_id.grade_id.name if rec.employee_id.grade_id else "N/A",
                rec.employee_id.bank_account_id.bank_id.name if rec.employee_id.bank_account_id else "N/A",
                rec.employee_id.bank_account_id.acc_number if rec.employee_id.bank_account_id else "N/A",
                basic,
                gross,
                rec.net_wage,
                SWIS_MPCS_PEEMADI,
                AL_HUDA_MPCS,
                CTSS_NASENI,
                CTSS_PEEMADI,
                FMBN_RENOVATION,
                NASENI_CSL,
                NHF,
                TSAN,
                NASU,
                SSAUTHRIAI,
                FIDELITY_DEBT,
                rec.department_id.name if rec.department_id else "N/A",
            ))

        # Create Excel file
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        sheet = workbook.add_worksheet("Payroll Advice")

        # Formats
        money_format = workbook.add_format({'num_format': '#,##0.00', 'align': 'left'})
        text_format = workbook.add_format({'align': 'left'})
        header_format = workbook.add_format({'bold': True, 'align': 'left'})

        # Headers
        sheet.merge_range("A1:H1", "NATIONAL AGENCY FOR SCIENCE AND ENGINEERING INFRASTRUCTURE", header_format)
        sheet.merge_range("A2:H2", "IDU INDUSTRIAL LAYOUT, ABUJA", header_format)
        sheet.merge_range("A3:H3", f"PAYROLL DETAIL REPORT FOR {calendar.month_name[selected_month]} {selected_year}", header_format)

        headers = [
            "SNO",
            "STAFF ID",
            "STAFF NAME",
            "GRADELEVEL",
            "BANK",
            "ACC NO",
            "BASIC",
            "GROSS PAY",
            "Net Pay",
            "SWIS_MPCS_PEEMADI",
            "AL_HUDA_MPCS",
            "CTSS_NASENI",
            "CTSS_PEEMADI",
            "FMBN_RENOVATION",
            "NASENI_CSL",
            "NHF",
            "TSAN",
            "NASU",
            "SSAUTHRIAI",
            "FIDELITY_DEBT",
            "CENTRE",
        ]

        for col, header in enumerate(headers):
            sheet.write(5, col, header, header_format)

        # Write data
        for row, data in enumerate(PAYROLL_DATA, start=6):
            for col, value in enumerate(data):
                if col in range(6, 19):  # Amount columns (BASIC to FIDELITY_DEBT)
                    sheet.write(row, col, value, money_format)
                else:
                    sheet.write(row, col, value, text_format)

        workbook.close()

        file_data = base64.b64encode(output.getvalue()).decode("utf-8")
        output.close()

        filename = f"Payroll Advice {calendar.month_name[selected_month]} {selected_year}"
        self.write({"file_name": f"{filename}.xlsx", "file_data": file_data})

        return {
            "type": "ir.actions.act_url",
            "url": f"/web/content/?model=payroll.advice.generate&id={self.id}&field=file_data&filename_field=file_name&download=true",
            "target": "self",
        }
