from odoo import models, fields

class AssetLocation(models.Model):
    _name = 'asset.location'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Asset Location'

    name = fields.Char('Location Name')