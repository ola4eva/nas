from odoo import models, fields, _


class EmployeeState(models.Model):
    _name = 'naseni_hr.state'
    _description = 'Employee State and Local Government'

    name = fields.Char(string="State", tracking=True)
    lga_ids = fields.One2many('naseni_hr.lga', 'state_id', string='LGA', tracking=True)

    def name_get(self):
        res = []
        for record in self:
            name = record.name
            if not record.name.startswith("State"):
                name = "State %s " % record.name
            res.append((record.id, name,))
        return res


class EmployeeLga(models.Model):
    _name = 'naseni_hr.lga'
    _description = 'Sate LGA'

    name = fields.Char('LGA')
    state_id = fields.Many2one('naseni_hr.state', string='State')

    def name_get(self):
        res = []
        for record in self:
            name = record.name
            if record.state_id:
                name = "%s - %s" % (record.state_id.name if record.state_id.name.startswith("State") else "State %s" %
                                    record.state_id.name, record.name if record.name.startswith("Lga") else "Lga %s" % record.name)
            res.append((record.id, name,))
        return res