{
    'name': 'Employee History',
    'version': '0.0.2',
    'summary': 'Adds a history tab to the employee form with specific fields and logic.',
    'description': """
        - Adds a History tab to the Employee form
        - Computes next anniversary date and notification date
        - Allows confirming an employee
    """,
    'author': 'MOB - Ifeanyi Nneji',
    'website': 'https://www.mattobell.net/',
    'category': 'Human Resources',
    'depends': ['hr'],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_employee_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
