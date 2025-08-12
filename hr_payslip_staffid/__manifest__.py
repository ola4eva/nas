{
    'name': 'Payslip Staff ID',
    'version': '1.0',
    'depends': ['hr_payroll'],
    'author': 'Your Name or Company',
    'category': 'Human Resources',
    'description': 'Displays Staff ID on Payslip form, report, and export.',
    'data': [
        'security/ir.model.access.csv',
        'security/hr_payslip_staffid_rules.xml',
        'views/hr_payslip_views.xml',
        'reports/report_payslip_inherit.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}