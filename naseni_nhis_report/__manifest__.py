# -*- coding: utf-8 -*-
{
    "name": "NHIS Report",
    "version": "18.0.1.0.0",
    "summary": "NHIS Report",
    "category": "Payroll",
    "license": "LGPL-3",
    "description": """
NHIS Report
========================
    """,
    "author": "HyperIT Consultants",
    "website": "https://www.yourcompany.com",
    "category": "Uncategorized",
    "version": "0.1",
    "depends": ["hr_payroll", "naseni_hr"],
    "data": [
        "security/ir.model.access.csv",
        "wizard/views/nhis_wizard_view.xml",
        "wizard/views/nhis_wizard_action.xml",
        "wizard/views/nhis_wizard_menu.xml",
    ],
}
