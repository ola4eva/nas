{
    "name": "POS Category Multi-Company",
    "version": "18.0.1.0.0",
    "summary": "Add company_id to POS categories and restrict visibility per company.",
    "author": "Your Name",
    "website": "",
    "category": "Point of Sale",
    "depends": ["point_of_sale"],
    "data": [
        "security/ir.model.access.csv",
        "security/pos_category_rules.xml",
        "views/pos_category_views.xml"
    ],
    "installable": True,
    "application": False,
    "license": "LGPL-3"
}