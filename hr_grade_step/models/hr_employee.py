# -*- coding: utf-8 -*-

from odoo import models, fields


class HrEmployeeBase(models.AbstractModel):
    _inherit = 'hr.employee.base'

    grade_id = fields.Many2one('hr.employee.grade', string='Grade')
    step_id = fields.Many2one('hr.employee.step', string='Step', domain="[('grade_id', '=', grade_id)]")