from odoo import models
import logging

_logger = logging.getLogger(__name__)


class HrEmployee(models.Model):

    _inherit = "hr.employee"

    def _compute_display_name(self):
        for employee in self:
            use_staff_id = self.env.context.get('show_staff_id')
            for employee in self:
                employee.display_name = employee.staff_id if use_staff_id and employee.staff_id else employee.name
                
            
