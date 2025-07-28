from odoo import api, models, fields


class StockRejectionReason(models.Model):
    _name = "stock.rejection.reason"
    _description = 'Reason for Rejecting Requests'

    name = fields.Char('Name', required=True, translate=True)
    active = fields.Boolean('Active', default=True)


class StockPickingRejection(models.TransientModel):
    _name = 'stock.picking.rejected'
    _description = 'Get Rejection Reason'

    rejection_reason_id = fields.Many2one(
        'stock.rejection.reason', 'Rejection Reason')

    def action_rejection_reason_apply(self):
        leads = self.env['stock.picking'].browse(
            self.env.context.get('active_ids'))
        leads.write({'rejection_reason': self.rejection_reason_id.id})
        return leads.button_reject()
