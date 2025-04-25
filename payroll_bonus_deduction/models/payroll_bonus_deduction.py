# -*- coding: utf-8 -*-
from datetime import date
from odoo import models, fields


class PayrollBonusDeduction(models.Model):
    _name = 'payroll.bonus.deduction'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Payroll Bonuses & Deductions'

    name = fields.Char(string="Name")
    note = fields.Text('Description')
    employee_id = fields.Many2one(
        comodel_name="hr.employee", string="Employee")
    input_type_id = fields.Many2one(
        comodel_name="payroll.otherinput.type", string="Type")
    date = fields.Date(string='Date', default=date.today())
    state = fields.Selection([
        ('draft', 'New'),
        ('confirm', 'Confirmed')
    ], string='State', default="draft", readonly="1", tracking=True)

    def action_confirm(self):
        return self.write({'state': "confirm"})
