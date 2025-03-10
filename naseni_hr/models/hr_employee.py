# -*- coding: utf-8 -*-

from odoo import models, fields, api


class HrEmployee(models.Model):
    _inherit = 'hr.employee'
    
    institute_id = fields.Many2one(comodel_name='naseni_hr.institute', string="Institute")
    pfa_id = fields.Many2one(comodel_name='naseni_hr.pfa', string="PFA")
    pension_pin = fields.Char('Pension PIN')