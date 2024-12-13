{
    'name': 'Payroll  and Payslip Enhancements',
    'version': '1.2.4',
    'category': 'Human Resources/Payroll Management',
    'summary': 'Enhanced payroll management with secondary currency support, payslip signatures, and detailed salary information on contracts',
    'description': """
        This module introduces comprehensive secondary currency functionality for payroll, enabling organizations to manage wages in both primary and secondary currencies. 
        It also enhances payslip records with signature capabilities and adds detailed fields for salary information in employee contracts.
    """,
    'author': 'MOB - Ifeanyi Nneji',
    'website': 'https://www.mattobell.net/',
    'depends': [
        'hr_contract',
        'hr_payroll',
        'account_accountant',
        'base',
    ],
    'data': [
        'views/hr_contract_views.xml',
        'views/res_company_views.xml',
        'views/hr_payslip_views.xml',
        'views/report_payslip_templates.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
