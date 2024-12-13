from odoo import models, fields, api
from odoo.exceptions import ValidationError

class ApprovalNotification(models.Model):
    _name = 'approval.notification'
    _description = 'Approval Notification'

    name = fields.Char(string='Name')
    user_ids = fields.Many2many(
        'res.users', 
        string='Users to Notify', 
        relation='approval_notification_users_rel',
        column1='notification_id', 
        column2='user_id'
    )
    partner_ids = fields.Many2many(
        'res.partner', 
        string='Partners to Notify'
    )
    approvers = fields.Many2many(
        'res.users', 
        string='Approvers', 
        relation='approval_notification_approvers_rel',
        column1='notification_id', 
        column2='approver_id'
    )
    state = fields.Selection([
        ('first_approval', 'First Level Approval'),
        ('second_approval', 'Second Level Approval'),
        ('third_approval', 'Third Level Approval'),
    ], string='Approval State')

    @api.constrains('state')
    def _check_unique_state(self):
        for record in self:
            if self.search([('state', '=', record.state), ('id', '!=', record.id)]):
                raise ValidationError(f"A notification for '{record.state}' already exists.")
