from odoo import models, fields, api, _
from odoo import models, fields, api
# from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, ValidationError
from urllib.parse import urljoin, urlencode
from urllib.parse import urljoin, urlencode
from odoo import models, api

import time


class account_cash_advance(models.Model):
    _inherit = 'cash.advance'

    # @api.multi
    def validate(self):
        cash = self
        if not cash.advance:
            raise ValidationError('You can not confirm cash advance if advance is zero.')
        if cash.amount_total + cash.emp_id.balance > cash.emp_id.limit:
            raise UserError(_('This advance request is over your allowed limit.'))
        mail_template = self.env.ref('ng_cash_advance_notifications.cash_advance_approval_notify')
        manager_group = self.env.ref('account_cash_advance.advance_manager')
        for content in manager_group.users:
            recipients = content.login
            url = self.request_link()
            mail_template.with_context({'recipient': recipients, 'url': url}).send_mail(self.id, force_send=True)
        return self.write({'state': 'open'})

    # @api.multi
    def approve(self):
        FINANCE_EMAIL = 'ola4eva2001@gmail.com'
        cash = self
        if cash.amount_total + cash.emp_id.balance > cash.emp_id.limit:
            raise ValidationError(_('Error!, This advance request is over your allowed limit.'))
        date = time.strftime('%Y-%m-%d')
        obj_emp = self.env['hr.employee']
        ids2 = obj_emp.search([('user_id', '=', self.env.user.id)], limit=1)
        manager = ids2 and ids2.id or False
        mail_template = self.env.ref('ng_cash_advance_notifications.cash_advance_notify_account')
        requester_notification_template = self.env.ref('ng_cash_advance_notifications.cash_advance_approve_notify_requester')
        requester_notification_template.with_context(recipient=self.emp_id.work_email, url=self.request_link()).send_mail(self.id, force_send=True)
        mail_template.with_context(recipient=FINANCE_EMAIL, url=self.request_link()).send_mail(self.id, force_send=True)
        manager_group = self.env.ref('account.group_account_manager')
        for content in manager_group.users:
            recipients = content.login
            url = self.request_link()
            mail_template.with_context({'recipient': recipients, 'url': url}).send_mail(self.id, force_send=True)
        return self.write({'state': 'approve', 'manager_id': manager, 'approval_date': date})

    def request_link(self):
        # Get the base URL of the Odoo instance
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')

        # Get the references for the required menu and action
        menu_id = self.env.ref('account_cash_advance.action_account_cash_advance_menu').id
        action_id = self.env.ref('account_cash_advance.action_account_cash_advance').id

        # Construct the URL fragment
        fragment = {
            'base_url': base_url,
            'menu_id': menu_id,
            'model': 'cash.advance',
            'view_type': 'form',
            'action': action_id,
            'id': self.id,
        }

        # Construct the query parameters
        query = {'db': self.env.cr.dbname}

        # Join the base URL with the constructed fragment and query
        res = urljoin(base_url, "/web?%s#%s" % (urlencode(query), urlencode(fragment)))

        return res


    # def request_link(self):
    #     fragment = {}
    #     base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
    #     model_data = self.env['ir.model.data']
    #     fragment.update(base_url=base_url)
    #     fragment.update(
    #         menu_id=model_data.get_object_reference('account_cash_advance', 'action_account_cash_advance_menu')[1])
    #     fragment.update(model='cash.advance')
    #     fragment.update(view_type='form')
    #     fragment.update(
    #         action=model_data.get_object_reference('account_cash_advance', 'action_account_cash_advance')[1])
    #     fragment.update(id=self.id)
    #     query = {'db': self.env.cr.dbname}
    #     res = urljoin(base_url, "/web?%s#%s" % (urlencode(query), urlencode(fragment)))
    #     return res


class HrEmployee(models.Model):


    _inherit = 'hr.employee'
    limit_naira = fields.Float("Limit(Naira)")
    limit = fields.Float(string='Expense Limit',
                         help='Limit amount of employee for expense advance.', compute='convert_naira',store=True)
    @api.depends('limit_naira')
    def convert_naira(self):
        for thin in self:
            if thin.limit_naira:
                try:
                    thin.limit = float(thin.limit_naira) / float(thin.company_id.purchase_currency_naira)
                except ZeroDivisionError:
                    thin.limit = 0.0


class Rescompany(models.Model):
    _inherit = 'res.company'
    purchase_currency_naira = fields.Float("Purchase Currency Naira")
