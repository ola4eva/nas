{
    'name': 'Custom Purchase Approval',
    'version': '0.0.6',
    'summary': 'Custom approval workflow for Purchase Orders',
    'description': 'Adds extra approval states and notifications for Purchase Orders based on PO value.',
    'author': 'MOB - Ifeanyi Nneji',
    'website': 'https://www.mattobell.net/',
    'depends': ['purchase'],
    'data': [
        'security/ir.model.access.csv',
        'views/purchase_order_views.xml',
        'views/approval_notification_views.xml',
        'data/approval_notification_email_template.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}

