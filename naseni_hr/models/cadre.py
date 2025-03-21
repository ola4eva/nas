from odoo import models, fields, api

class HrCadre(models.Model):
    _name = 'naseni_hr.cadre'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Cadre'

    name = fields.Char('Name')