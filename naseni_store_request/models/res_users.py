from odoo import models


class ResUsers(models.Model):

    _inherit = "res.users"

    def get_user_department(self):
        related_employee = self.env["hr.employee"].search(
            [("user_id", "=", self.id)], limit=1
        )
        if not related_employee:
            return False
        department_id = related_employee.department_id
        return department_id and department_id.ids
