from odoo import models, fields


class NextOfKinRelationship(models.Model):
    _name = "nok.relationship"
    _description = "Next Of Kin Relationship"

    name = fields.Char("Name")
