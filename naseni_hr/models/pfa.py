from odoo import models, fields

class PensionFundAdministrator(models.Model):
    _name = 'naseni_hr.pfa'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Pension Fund Administrator'

    name = fields.Char('Name')