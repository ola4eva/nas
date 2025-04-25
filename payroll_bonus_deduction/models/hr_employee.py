from odoo import models, fields


class HrEmployee(models.Model):

    _inherit = 'hr.employee'

    def _get_other_input(self, employee, code="LTNS"):
        return 6500