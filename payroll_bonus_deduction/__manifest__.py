# -*- coding: utf-8 -*-
{
    'name': "Payroll Bonuses and Deductions",

    'summary': """
        Manage bonuses and deductions for employees.""",

    'description': """
        Manage bonuses and deductions for employees.
        - Add PayrollOtherInputType model
        - Add PayrollOtherInput model
        - Add PayrollBonusDeduction model
        - Add function on employee model to compute the deductions or bonuses for the employee
    """,

    'author': "HyperIT Consultants",
    'website': "https://",

    'category': 'Uncategorized',
    'version': '0.1',

    'depends': [
        'hr_payroll'
        'naseni_hr',
    ],

    'license': 'LGPL-3',

    'data': [
        'data/deduction_server_action.xml',
        'security/payroll_bonus_deduction_groups.xml',
        'security/ir.model.access.csv',
        'views/payroll_bonus_deduction_views.xml',
    ],
}
