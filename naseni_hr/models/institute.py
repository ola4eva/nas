from odoo import models, fields


class NaseniInstitute(models.Model):
    _name = "naseni_hr.institute"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Naseni Institute"

    name = fields.Char('Institute')
