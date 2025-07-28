{
    'name': 'GIFMIS Payment Report',
    'version': '1.0',
    'depends': ['hr_payroll', 'naseni_hr'],
    'author': 'HyperIT Consultants, Olalekan Babawale',
    'category': 'Payroll',
    'license': 'LGPL-3',
    'data': [
        'security/ir.model.access.csv',
        'views/gifmis_report_wizard_views.xml',
        'views/hr_payslip_views.xml',
        'views/hr_payslip_run_views.xml',
    ],
    'installable': True,
}
