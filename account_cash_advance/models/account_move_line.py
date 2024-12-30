from odoo import models, fields


class account_moveline(models.Model):
    _inherit = "account.move.line"
    _description = "Account Move line"

    name = fields.Char(string="Name", required=True)
    ref = fields.Char(related="move_id.ref", string="Reference", store=True)
