from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    employee_retirement_reminder_name = fields.Char(
        string="Reminder Name",
        config_parameter="naseni_hr.employee_retirement_reminder_name",
    )
    employee_retirement_reminder_email = fields.Char(
        string="Reminder Email",
        config_parameter="naseni_hr.employee_retirement_reminder_email",
    )

    def get_values(self):
        ICP = self.env["ir.config_parameter"].sudo()
        return {
            "employee_retirement_reminder_name": ICP.get_param(
                "naseni_hr.employee_retirement_reminder_name"
            ),
            "employee_retirement_reminder_email": ICP.get_param(
                "naseni_hr.employee_retirement_reminder_email"
            ),
        }
