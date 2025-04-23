# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountAsset(models.Model):
    _inherit = 'account.asset'

    location_id = fields.Many2one(comodel_name='asset.location', string="Asset Location")
    ref = fields.Char('Asset Number')