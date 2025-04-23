from odoo import models, fields, _


class EmployeeGrade(models.Model):
    _name = 'hr.employee.grade'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Employee Grade'

    name = fields.Char(string="Grade", tracking=True)
    note = fields.Text('Description', tracking=True)
    step_ids = fields.One2many('hr.employee.step', 'grade_id', string='Step', tracking=True)

    def name_get(self):
        res = []
        for record in self:
            name = record.name
            if not record.name.startswith("Grade"):
                name = "Grade %s " % record.name
            res.append((record.id, name,))
        return res


class EmployeeStep(models.Model):
    _name = 'hr.employee.step'
    _description = 'Employee Step'

    name = fields.Char('Step')
    note = fields.Text('Description')
    grade_id = fields.Many2one('hr.employee.grade', string='Grade')
    basic = fields.Float('Basic')

    def name_get(self):
        res = []
        for record in self:
            name = record.name
            if record.grade_id:
                name = "%s - %s" % (record.grade_id.name if record.grade_id.name.startswith("Grade") else "Grade %s" %
                                    record.grade_id.name, record.name if record.name.startswith("Step") else "Step %s" % record.name)
            res.append((record.id, name,))
        return res
