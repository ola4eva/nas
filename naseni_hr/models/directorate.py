from odoo import models, fields, api

class HrDirectorate(models.Model):
    _name = 'naseni_hr.directorate'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Directorate'

    name = fields.Char('Name')