# -*- coding: utf-8 -*-
{
    "name": "Payroll Summary Report",
    "version": "18.0.1.0.0",
    "summary": "Payroll Summary Report",
    "category": "Payroll",
    "license": "LGPL-3",
    "description": """
        Payroll Summary Report
    """,
    "author": "HyperIT Consultants",
    "website": "https://www.yourcompany.com",
    "category": "Uncategorized",
    "version": "0.1",
    "depends": ["hr_payroll", "naseni_hr"],
    "data": [
        "security/ir.model.access.csv",
        "wizard/generate_payroll_summary_report_views.xml",
    ],
}
