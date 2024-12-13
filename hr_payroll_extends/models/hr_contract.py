from odoo import models, fields, api
from odoo.exceptions import ValidationError

import logging

logging.basicConfig(level=logging.INFO)

class HrContract(models.Model):
    _inherit = 'hr.contract'
    
    # Allowances
    earned_leave_allowance = fields.Float(string='Earned Leave Allowance (Amount)', default=0.00)
    house_rent_allowance = fields.Float(string='House Rent Allowance (%)', default=75.00)
    utility_allowance = fields.Float(string='Utility (%)', default=12.50)
    meal_allowance = fields.Float(string='Meal Allowance (%)', default=25.00)
    entertainment_allowance = fields.Float(string='Entertainment Allowance (%)', default=12.50)
    transport_allowance = fields.Float(string='Transport Allowance (%)', default=25.00)

    # Deductions
    pension_company_contribution = fields.Float(string='Pension Company Contribution (%)', default=7.50)
    pension_employee_contribution = fields.Float(string='Pension Employee Contribution (%)', default=7.50)
    secondary_currency_id = fields.Many2one(
        'res.currency',
        string='Secondary Currency',
        tracking=True,
        default=lambda self: self.env.company.payroll_currency_id,
        required=True,
    )

    wage_secondary = fields.Monetary(
        string='Wage in Secondary Currency',
        currency_field='secondary_currency_id',
        tracking=True,
        store=True,
        required=True,
    )
    
    # Remove compute from wage field definition
    wage = fields.Monetary(
        string='Wage',
        currency_field='currency_id',
        tracking=True,
        store=True,
        readonly=True,
    )
    
    # Inside the HrContract class
    saving_scheme_employee = fields.Float(
        string='Saving Scheme Employee (%)', 
        default=0.00, 
        help="Percentage contribution by the employee towards the saving scheme."
    )
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'wage_secondary' in vals and 'secondary_currency_id' in vals:
                # Convert wage_secondary to wage before creation
                currency_secondary = self.env['res.currency'].browse(vals['secondary_currency_id'])
                company = self.env['res.company'].browse(vals.get('company_id') or self.env.company.id)
                try:
                    wage_value = currency_secondary._convert(
                        float(vals['wage_secondary']),
                        company.currency_id,
                        company,
                        fields.Date.today()
                    )
                    vals['wage'] = wage_value
                except:
                    vals['wage'] = float(vals['wage_secondary'])
        return super().create(vals_list)

    def write(self, vals):
        if 'wage_secondary' in vals or 'secondary_currency_id' in vals:
            for record in self:
                currency_secondary = self.env['res.currency'].browse(
                    vals.get('secondary_currency_id', record.secondary_currency_id.id)
                )
                wage_secondary = vals.get('wage_secondary', record.wage_secondary)
                company = record.company_id or self.env.company
                try:
                    wage_value = currency_secondary._convert(
                        float(wage_secondary),
                        company.currency_id,
                        company,
                        fields.Date.today()
                    )
                    vals['wage'] = wage_value
                except:
                    vals['wage'] = float(wage_secondary)
        return super().write(vals)

    @api.onchange('wage_secondary', 'secondary_currency_id')
    def _onchange_wage_secondary(self):
        if self.wage_secondary and self.secondary_currency_id and self.company_id:
            try:
                self.wage = self.secondary_currency_id._convert(
                    self.wage_secondary,
                    self.company_id.currency_id,
                    self.company_id,
                    fields.Date.today()
                )
            except:
                self.wage = self.wage_secondary

    @api.constrains('wage_secondary')
    def _check_wage_secondary(self):
        for record in self:
            if not record.wage_secondary or record.wage_secondary <= 0:
                raise ValidationError("Secondary wage must have a positive value.")

    @api.onchange('company_id')
    def _onchange_company_id(self):
        if self.company_id and self.company_id.payroll_currency_id:
            self.secondary_currency_id = self.company_id.payroll_currency_id