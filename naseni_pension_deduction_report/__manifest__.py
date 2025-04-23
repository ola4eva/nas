# -*- coding: utf-8 -*-
{
    "name": "Pension Deduction Report",
    "version": "18.0.1.0.0",
    "summary": "Pension Deduction Report",
    "category": "Payroll",
    "license": "LGPL-3",
    "description": """
Pension Deduction Report
========================
    """,
    "author": "HyperIT Consultants",
    "website": "https://www.yourcompany.com",
    "category": "Uncategorized",
    "version": "0.1",
    "depends": ["hr_payroll","naseni_hr"],
    "data": [
        "security/ir.model.access.csv",
        "wizard/views/pension_deduction_wizard_view.xml",
        "wizard/views/pension_deduction_wizard_action.xml",
        "wizard/views/pension_deduction_wizard_menu.xml",
    ],
}
