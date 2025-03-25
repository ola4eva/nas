# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def get_employees_with_wrong_steps(cr, ctx):
    env = api.Environment(cr, SUPERUSER_ID, ctx)
    return (
        env["hr.employee"]
        .search([])
        .filtered(
            lambda emp: emp.grade_id
            and emp.step_id
            and emp.grade_id != emp.step_id.grade_id
        )
    )


class HrEmployeeBase(models.AbstractModel):
    _inherit = "hr.employee.base"

    grade_id = fields.Many2one("hr.employee.grade", string="Grade")
    step_id = fields.Many2one(
        "hr.employee.step", string="Step", domain="[('grade_id', '=', grade_id)]"
    )

    @api.model
    def remap_wrong_grades_steps(self):
        """Remap Steps for Employees with Wrong Steps"""

        _logger.info("Starting the remapping of employee steps...")

        # Before cleanup
        employees_with_wrong_steps = get_employees_with_wrong_steps(
            self._cr, self._context.copy()
        )
        _logger.info(
            f"{len(employees_with_wrong_steps)} Employees with wrong steps before cleanup...: {employees_with_wrong_steps.mapped('name')}"
        )
        for employee in employees_with_wrong_steps:
            _logger.info(
                f"Employee {employee.name} with grade {employee.grade_id.name} has a wrong step: {employee.step_id.name} mapped to Grade {employee.step_id.grade_id.name}"
            )
            # Get the right step for the mapping
            step_id = (
                self.env["hr.employee.step"]
                .sudo()
                .search(
                    [
                        ("name", "=", employee.step_id.name),
                        ("grade_id", "=", employee.grade_id.id),
                    ]
                )
            )
            step_id and employee.update({"step_id": step_id.id})

        # After cleanup
        employees_with_wrong_steps = get_employees_with_wrong_steps(
            self._cr, self._context.copy()
        )
        _logger.info(
            f"{len(employees_with_wrong_steps)} employees with wrong steps after cleanup...: {employees_with_wrong_steps.mapped('name')}"
        )
        _logger.info("Starting the remapping of employee steps...")
        return True
