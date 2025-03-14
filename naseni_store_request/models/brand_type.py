# -*- coding: utf-8 -*-

from odoo import fields, models, _


class BrandType(models.Model):
    _name = "brand.type"
    _description = 'Make/Brand'

    name = fields.Char('Name', required=True, translate=True)
    active = fields.Boolean('Active', default=True)
