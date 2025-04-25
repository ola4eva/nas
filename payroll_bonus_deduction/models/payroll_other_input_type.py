# -*- coding: utf-8 -*-

from odoo import models, fields


class PayrollOtherInputType(models.Model):
    _name = 'payroll.otherinput.type'
    _inherit =['mail.thread', 'mail.activity.mixin']
    _description = 'Payroll Other Input Types'
    _sql_constraints = [
        ('code_unique', 'unique (code)', 'Code should be unique!'),
    ]

    name = fields.Char(string="Name", required=True, readonly=True, states={'draft': [('readonly', False)]})
    internal_type = fields.Selection(selection=[
        ('deduction', 'Deduction'),
        ('bonus', 'Bonus'),
    ], string="Type", required=True, readonly=True, states={'draft': [('readonly', False)]})
    code = fields.Char(string="Code", help="Example: LTN for lateness", required=True, readonly=True, states={'draft': [('readonly', False)]})
    note = fields.Text(string="Description", required=True, readonly=True, states={'draft': [('readonly', False)]})
    state = fields.Selection([
        ('draft', 'New'),
        ('confirm', 'Confirmed'),
    ], string='State', default="draft", readonly=True, tracking=True)

    def action_confirm(self):
        return self.write({"state": "confirm"})
