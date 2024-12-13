import logging
from odoo import models, fields, api
from odoo.exceptions import AccessError

_logger = logging.getLogger(__name__)

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    state = fields.Selection(selection_add=[
        ('first_approval', 'First Level Approval'),
        ('second_approval', 'Second Level Approval'),
        ('third_approval', 'Third Level Approval'),
    ], ondelete={'first_approval': 'set default', 'second_approval': 'set default', 'third_approval': 'set default'})

    first_approver_ids = fields.Many2many(
        'res.users',
        'purchase_order_first_approver_rel',
        'order_id',
        'user_id',
        string='First Level Approvers',
        compute='_compute_approvers',
        store=True
    )
    second_approver_ids = fields.Many2many(
        'res.users',
        'purchase_order_second_approver_rel',
        'order_id',
        'user_id',
        string='Second Level Approvers',
        compute='_compute_approvers',
        store=True
    )
    third_approver_ids = fields.Many2many(
        'res.users',
        'purchase_order_third_approver_rel',
        'order_id',
        'user_id',
        string='Third Level Approvers',
        compute='_compute_approvers',
        store=True
    )

    def get_minimum_approval_amount(self):
        """Get the approval threshold amount from settings"""
        param = self.env['ir.config_parameter'].sudo()
        _logger.info(f"Minimum Amount Parameter: {param}")
        amount = float(param.get_param('purchase.po_double_validation_amount', default='0.0'))
        _logger.info(f"Minimum amount Value: {amount}")
        return amount

    @api.model
    def create(self, vals):
        order = super(PurchaseOrder, self).create(vals)
        order.write({'state': 'sent'})
        return order

    def button_confirm(self):
        for order in self:
            if order.state == 'draft':
                order.write({'state': 'sent'})
            if order.state == 'sent':
                self.write({'state': 'first_approval'})
        return super(PurchaseOrder, self).button_confirm()

    @api.depends('state')
    def _compute_approvers(self):
        for order in self:
            _logger.info(f"Computing approvers for order {order.id}, state: {order.state}")
            if order.state == 'first_approval':
                approvers = self._get_approvers('first_approval')
                order.first_approver_ids = approvers
            elif order.state == 'second_approval':
                approvers = self._get_approvers('second_approval')
                order.second_approver_ids = approvers
            elif order.state == 'third_approval':
                approvers = self._get_approvers('third_approval')
                order.third_approver_ids = approvers

    def _get_approvers(self, state):
        _logger.info(f"Searching for approval notification with state: {state}")

        notification = self.env['approval.notification'].search([('state', '=', state)], limit=1)

        if notification:
            _logger.info(f"Notification found for state '{state}'. Approvers: {[user.name for user in notification.approvers]}")
            return notification.approvers
        else:
            _logger.warning(f"No approval notification found for state '{state}'")
            return []

    def action_first_approval(self):
        if self.env.user not in self.first_approver_ids:
            _logger.info(f"First Approval list: {self.first_approver_ids}")
            raise AccessError("You are not authorized to approve at this level.")
        self.write({'state': 'second_approval'})
        self._send_approval_notification('first_approval')

    def action_second_approval(self):
        if self.env.user not in self.second_approver_ids:
            raise AccessError("You are not authorized to approve at this level.")
        if self.amount_total >= self.get_minimum_approval_amount():
            self.write({'state': 'third_approval'})
        else:
            self.write({'state': 'purchase'})
        self._send_approval_notification('second_approval')

    def action_third_approval(self):
        if self.env.user not in self.third_approver_ids:
            raise AccessError("You are not authorized to approve at this level.")
        self.write({'state': 'purchase'})
        self._send_approval_notification('third_approval')

    def _send_approval_notification(self, state):
        notifications = self.env['approval.notification'].search([('state', '=', state)])
        _logger.info(f"Sending approval notification for state: {state}")
        
        for notification in notifications:
            notifier_user_names = ', '.join(notification.user_ids.mapped('name'))
            notifier_partner_names = ', '.join(notification.partner_ids.mapped('name'))
            _logger.info(f"Notifiers (Users): {notifier_user_names}")
            _logger.info(f"Notifiers (Partners): {notifier_partner_names}")

            for user in notification.user_ids:
                template = self.env.ref('custom_purchase_approval.approval_notification_email_template')
                template.send_mail(self.id, force_send=True, email_values={'email_to': user.email})
            
            message_body = f"""
            Approval Notification for {state.replace('_', ' ').title()}:
            Notifiers (Users): {notifier_user_names or 'None'}
            Notifiers (Partners): {notifier_partner_names or 'None'}
            """
            self.message_post(body=message_body)
