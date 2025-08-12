{
    "name": "HR Payroll Excel Report",
    "version": "1.0",
    "depends": ["hr_payroll", "report_xlsx"],
    "author": "Your Company",
    "category": "Human Resources",
    "description": "Generates payroll Excel reports with Employee Name, Staff ID, and Net Pay",
    "data": [
        "views/payroll_report_wizard_view.xml",
        "reports/payroll_excel_report.xml"
    ],
    "installable": True,
    "application": False
}