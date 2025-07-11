from odoo import models, fields

NEXT_OF_KIN_SELECTION = [
    ("son", "Son"),
    ("daughter", "Daughter"),
    ("father", "Father"),
    ("mother", "Mother"),
    ("husband", "Husband"),
    ("wife", "Wife"),
    ("pastor", "Pastor"),
    ("friend", "Friend"),
]


class NextOfKin(models.Model):
    _name = "naseni_hr.next_of_kin"
    _description = "Next Of Kin"

    name = fields.Char("Name")
    relationship = fields.Selection(
        selection=NEXT_OF_KIN_SELECTION, string="Relationship"
    )
    phone = fields.Char("Phone")
    employee_id = fields.Many2one("hr.employee", string="Employee")
