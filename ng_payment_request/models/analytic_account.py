from odoo import models, fields


class AnalyticAccount(models.Model):

    _inherit = 'account.analytic.account'

    user_ids = fields.Many2many('res.users', string='Informed Party')