# -*- coding: utf-8 -*-
{
    'name': "Staff Advance Approval Notifications",

    'summary': """Manage Staff Advance Notifications""",

    'description': """
        Module adds notifications at every stage of approval of staff advance requests
    """,

    'author': "Matt O'Bell Ltd",
    'website': "http://www.mattobell.net",

    'category': 'Uncategorized',
    'version': '0.1',
    'depends': [
        'base',
        # 'ng_approval_base',
        'account_cash_advance',
        # 'ng_double_approval_purchase'
    ],

    'data': [
        'views/views.xml',
        'views/templates.xml',
    ],
}
