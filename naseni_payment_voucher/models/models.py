# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class naseni_payment_voucher(models.Model):
#     _name = 'naseni_payment_voucher.naseni_payment_voucher'
#     _description = 'naseni_payment_voucher.naseni_payment_voucher'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100

