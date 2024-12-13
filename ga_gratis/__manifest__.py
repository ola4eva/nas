{
    "name": "Gratis",
    "summary": """Odoo without charges""",
    "description": """
        Odoo without charges
    """,
    "author": "My Company",
    "website": "http://www.yourcompany.com",
    "category": "hidden",
    "version": "1.0.1",
    "depends": ["base", "mail"],
    "data": [
        "data/ir_cron.xml",
    ],
    "license": "LGPL-3",
    "pre_init_hook": "pre_init_hook",
    "post_init_hook": "post_init_hook",
}
