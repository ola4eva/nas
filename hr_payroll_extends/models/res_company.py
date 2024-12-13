# res_company.py
from odoo import models, fields

class ResCompany(models.Model):
    _inherit = 'res.company'
    signature = fields.Binary("Signature for Payroll", attachment=True)
    payroll_currency_id = fields.Many2one(
        'res.currency',
        string='Default Payroll Currency',
        help='Default currency to be used for payroll calculations'
    )