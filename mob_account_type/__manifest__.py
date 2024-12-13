{
    'name': 'Account Type Custom',
    'version': '0.3',
    'summary': 'Account Type Custom Module',
    'description':
        """
        This module helps an organization to create account types.
        """,
    'category': 'Accounting',
    'author': 'MOB - Hamza Ilyas',
    'website': 'hamza.ilyaaaas@gmail.com',
    'depends': ['base', 'account'],
    'data': [
        'views/view.xml',
    ],
    'assets': {
        'web.assets_backend': [
            # 'mob_account_type/static/src/components/account_type_selection/account_type_selection.js',
            'mob_account_type/static/src/components/account_type_selection/custom_account_type_selection.xml',
            'mob_account_type/static/src/js/account_type_selection.js',
        ],
    },
    'installable': True,
    'auto_install': False,
}
