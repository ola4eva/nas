# -*- coding: utf-8 -*-
{
    'name': "Human Resources Extension",
    'summary': "Extension for the base human resources module",
    'description': """
        Extension for the base Human resources module. Features added by this module include:
        1. PFA Information of employee profile.
        2. Pension Identification Number (PIN) on employee profile.
        3. Add institute field to employee profile.
    """,
    'author': "HyperIT Consultants",
    'website': "https://www.yourcompany.com",
    'category': 'Uncategorized',
    'version': '18.0.1.0.1',
    'depends': ['hr'],
    'license': "LGPL-3",
    'data': [
        'security/ir.model.access.csv',
        'security/retirement_groups.xml',
        'data/ir_cron.xml',
        'views/pfa_views.xml',
        'views/institute_views.xml',
        'views/hr_employee_views.xml',
        'views/res_config_settings_views.xml',
        'views/directorate_views.xml',
        'views/cadre_views.xml',
        'views/res_state_views.xml',
        'views/nok_relationship_views.xml',
        'views/tax_state_views.xml',
    ],
}

