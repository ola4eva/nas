from odoo import models, fields, api

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    signature_image = fields.Binary(related='company_id.signature', string="Signature", readonly=True)
    
    def _get_report_base_filename(self):
        self.ensure_one()
        return 'Payslip - %s' % (self.employee_id.name)

class HrPayslipLine(models.Model):
    _inherit = 'hr.payslip.line'

    total_primary_currency = fields.Monetary(
        string='Total Amount (Primary Currency)',
        compute='_compute_currency_totals',
        store=True,
        currency_field='primary_currency_id'
    )
    total_secondary_currency = fields.Monetary(
        string='Total Amount (Secondary Currency)',
        compute='_compute_currency_totals',
        store=True,
        currency_field='secondary_currency_id'
    )
    primary_currency_id = fields.Many2one(
        'res.currency',
        related='slip_id.company_id.payroll_currency_id',
        string='Primary Currency'
    )
    secondary_currency_id = fields.Many2one(
        'res.currency',
        related='contract_id.secondary_currency_id',
        string='Secondary Currency'
    )
    amount = fields.Float(string='Amount', digits=(16, 2))
    
    @api.depends('amount', 'total', 'primary_currency_id', 'secondary_currency_id')
    def _compute_currency_totals(self):
        for line in self:
            if line.primary_currency_id:
                # Convert from company currency to primary (payroll) currency
                line.total_primary_currency = line.secondary_currency_id._convert(
                    line.total,
                    line.primary_currency_id,
                    line.slip_id.company_id,
                    line.slip_id.date_from,
                )
            else:
                line.total_primary_currency = line.total

            if line.secondary_currency_id:
                # Convert from company currency to secondary currency
                line.total_secondary_currency = line.secondary_currency_id._convert(
                    line.total,
                    line.secondary_currency_id,
                    line.slip_id.company_id,
                    line.slip_id.date_from,
                )
            else:
                line.total_secondary_currency = 0.0