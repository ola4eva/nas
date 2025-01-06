# -*- coding: utf-8 -*-
{
    'name': "HR Employee Grade and Step",

    'summary': """HR employee grade and step""",

    'description': """
        HR employee grade and step
    """,

    'author': "HyperIT Consultants.",
    
    'website': "http://obabawale.github.io",

    'category': 'HR',

    'version': '18.0.0.0.1',

    'depends': [
        'hr',
    ],

    'license': 'LGPL-3',

    'data': [
        'security/ir.model.access.csv',
        'data/grade_step_data.xml',
        'views/employee_grade_views.xml',
        'views/hr_employee_views.xml',
    ],
}
