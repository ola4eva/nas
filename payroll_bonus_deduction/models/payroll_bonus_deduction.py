# -*- coding: utf-8 -*-
from datetime import date
from odoo import models, fields, api


class PayrollBonusDeduction(models.Model):
    _name = 'payroll.bonus.deduction'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Payroll Bonuses & Deductions'

    name = fields.Char(string="Name", required=True)
    note = fields.Text('Description')
    employee_id = fields.Many2one(
        comodel_name="hr.employee", string="Employee", required=True)
    date = fields.Date(string='Date', default=date.today(), required=True)
    other_input_id = fields.Many2one('hr.payslip.input.type', string='Other Input', required=True)
    amount = fields.Float('Amount', default=0.0)
    state = fields.Selection([
        ('draft', 'New'),
        ('confirm', 'Confirmed')
    ], string='State', default="draft", readonly="1", tracking=True)

    def _action_confirm(self):
        return self.write({'state': "confirm"})

    def unlink(self):
        return super(PayrollBonusDeduction, self - self.filtered(lambda r: r.state != "draft")).unlink()

    def action_confirm(self):
        """Confirm entries in batch"""
        return (self - self.filtered(lambda r: r.state != 'draft'))._action_confirm()
