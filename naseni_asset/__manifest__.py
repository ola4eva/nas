# -*- coding: utf-8 -*-
{
    'name': "Fixed Asset Extension",
    'summary': "Extension for the base Account Asset module",
    'description': """
        Extension for the base Account Assetb module. Features added by this module include:
        1. Added Asset location to the assset configuration menu
        2. Added asset loaction.
    """,
    'author': "HyperIT Consultants",
    'website': "https://www.hyperitconsultant.com",
    'category': 'Uncategorized',
    'version': '0.2',
    'depends': ['account_asset'],
    'license': "LGPL-3",
    'data': [
        'security/ir.model.access.csv',
        'views/account_location_views.xml',
        'views/account_asset_views.xml',
    ],
}