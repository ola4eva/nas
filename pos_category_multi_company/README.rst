POS Category Multi-Company
==========================

This module:

- Adds a `company_id` field to POS Categories (`pos.category`)
- Restricts visibility so users only see categories for their company
- Uses a record rule to enforce this on all standard users

Installation:
-------------

1. Copy `pos_category_multi_company` to your Odoo `addons_path`
2. Update Apps list and install it
3. Edit your existing categories to set their company, if needed
