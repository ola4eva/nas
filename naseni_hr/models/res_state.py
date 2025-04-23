from odoo import models, fields, _


class ResCountryState(models.Model):
    _inherit = 'res.country.state'

    lga_ids = fields.One2many(comodel_name='res.country.state.lga', inverse_name='state_id', string='LGAs')


class EmployeeLga(models.Model):
    _name = 'res.country.state.lga'
    _description = 'Local Government Area'

    name = fields.Char('LGA')
    country_id = fields.Many2one(comodel_name='res.country', string='country')
    state_id = fields.Many2one('res.country.state', string='State', domain="[('country_id', '=', country_id)]")

    def name_get(self):
        res = []
        for record in self:
            name = record.name + " Local Government"
            res.append((record.id, name,))
        return res