{
    "name": "Employee Cash Advances",
    "version": "0.0.1",
    "author": "Olalekan Babawale",
    "website": "http://obabawale.github.io",
    "description": """
Management of Various Cash Advances to Employees
================================================

Features
--------
* Salary Advances and Payment
* Pretty Cash Advances for Expense and Retirements
    """,
    "category": "Accounting & Finance",
    "sequence": 70,
    "depends": ["base", "accountant", "hr", "hr_expense", "hr_contract", "hr_payroll"],
    "data": [
        "security/account_salary_security.xml",
        "security/ir.model.access.csv",
        'report/cash_advance_report_view.xml',
        'views/res_company_view.xml',
        'views/ng_account_cash_view.xml',
        'views/cash_advance_view.xml',
        'views/hr_employee_view.xml',
        'views/hr_expense_retirement_view.xml',
        'views/ng_refund_advance_view.xml',
    ],
    "auto_install": False,
    "license": "LGPL-3",
    "installable": True,
    "application": False,
}
