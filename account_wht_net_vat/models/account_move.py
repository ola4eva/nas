from odoo import models, fields, api

class AccountMove(models.Model):
    _inherit = 'account.move'

    wht_rate = fields.Float(string="WHT Rate (%)", default=10.0)
    stamp_duty_rate = fields.Float(string="Stamp Duty Rate (%)", default=1.0)
    wht_account_id = fields.Many2one(
        'account.account',
        string='WHT Account',
        domain=[('user_type_id.type', '=', 'liability')],
        help="Account to record withholding tax."
    )
    stamp_duty_account_id = fields.Many2one(
        'account.account',
        string='Stamp Duty Account',
        domain=[('user_type_id.type', '=', 'liability')],
        help="Account to record stamp duty."
    )

    @api.onchange('invoice_line_ids', 'wht_rate', 'stamp_duty_rate')
    def _onchange_add_deduction_lines(self):
        if self.move_type not in ['in_invoice', 'out_invoice']:
            return

        # Remove existing WHT or Stamp lines
        self.invoice_line_ids = self.invoice_line_ids.filtered(lambda l: not l.name.startswith('[WHT]') and not l.name.startswith('[Stamp Duty]'))

        subtotal = sum(line.price_subtotal for line in self.invoice_line_ids)

        if self.wht_account_id and self.wht_rate > 0:
            wht_amount = round((subtotal * self.wht_rate) / 100, 2)
            self.invoice_line_ids += self.env['account.move.line'].new({
                'name': '[WHT] Withholding Tax',
                'quantity': 1,
                'price_unit': -wht_amount,
                'account_id': self.wht_account_id.id,
                'exclude_from_invoice_tab': False,
            })

        if self.stamp_duty_account_id and self.stamp_duty_rate > 0:
            stamp_amount = round((subtotal * self.stamp_duty_rate) / 100, 2)
            self.invoice_line_ids += self.env['account.move.line'].new({
                'name': '[Stamp Duty] (1%)',
                'quantity': 1,
                'price_unit': -stamp_amount,
                'account_id': self.stamp_duty_account_id.id,
                'exclude_from_invoice_tab': False,
            })
