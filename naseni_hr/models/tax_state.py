from odoo import models, fields


class NaseniTax(models.Model):
    _name = "naseni_hr.tax"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Naseni Tax State"

    name = fields.Char('Tax State')
