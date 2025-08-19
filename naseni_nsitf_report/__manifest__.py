# -*- coding: utf-8 -*-
{
    "name": "NSITF Report",
    "version": "18.0.1.0.0",
    "summary": "NSITF Report",
    "category": "Payroll",
    "license": "LGPL-3",
    "description": """
NSITF Report
========================
    """,
    "author": "HyperIT Consultants",
    "website": "https://www.yourcompany.com",
    "category": "Uncategorized",
    "version": "0.1",
    "depends": ["hr_payroll", "naseni_hr"],
    "data": [
        "security/ir.model.access.csv",
        "wizard/views/nsitf_wizard_view.xml",
        "wizard/views/nsitf_wizard_action.xml",
        "wizard/views/nsitf_wizard_menu.xml",
    ],
}
