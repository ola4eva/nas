from odoo import models, fields


class PaymentRequisitionCategory(models.Model):

    _name = "payment.requisition.category"
    _description = "Payment Requisition Category"

    name = fields.Char("Name")
    description = fields.Char("Description")

