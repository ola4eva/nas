{
    "name": "Odoo Enterprise Disable",
    "version": "18.0.0.0.1",
    "author": "Olalekan Babawale",
    "website": "https://obabawale.github.io",
    "description": "Disable odoo enterprise expiration for personal use",
    "summary": "This disables odoo enterprise expiration",
    "data": [],
    "depends": ["mail", "web_enterprise"],
    "license": "LGPL-3",
    "assets": {
        "web.assets_backend": [
            "disable_odoo_enterprise/static/src/enterprise_subscription_service.js",
        ]
    },
}
