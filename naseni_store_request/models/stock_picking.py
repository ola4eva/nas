# -*- coding: utf-8 -*-

from datetime import date
from werkzeug import urls
from urllib.parse import urlencode
from odoo.exceptions import UserError
from odoo import fields, models, api, _


class StockPicking(models.Model):
    _inherit = 'stock.picking'
    _order = 'create_date DESC'

    def _default_employee(self):
        return self.env['hr.employee'].sudo().search([('user_id', '=', self.env.uid)])

    state = fields.Selection(selection_add=[
        ('submit', 'Submitted'),
        ('approve', 'Line Manager Approved'),
        ('qa_qc_approve', 'QA/QC Approved'),
        ('waiting',),
        ('reject', 'Rejected'),
        ('cancel',)
    ])

    employee_id = fields.Many2one('hr.employee', 'Requesting Employee',
                                  states={'done': [('readonly', True)], 'cancel': [('readonly', True)]}, default=_default_employee,
                                  help="Default Owner")
    request_date = fields.Date(string='Date', default=date.today())
    department_id = fields.Many2one(
        comodel_name='hr.department', string='Department', related='employee_id.department_id')
    project_id = fields.Many2one(
        comodel_name='project.project', string='Project', index=True, ondelete='cascade', required=False)
    project_description = fields.Char('Project Description', copy=False)
    rejection_reason = fields.Many2one(
        'stock.rejection.reason', string='Rejection Reason', index=True, tracking=True)
    total_price = fields.Float(
        string='Total',
        compute='_total_price',
        readonly=True,
        store=True
    )
    need_approval = fields.Boolean(
        'Need Approval', tracking=True, copy=False)
    total_cost = fields.Float(
        string='Total Cost',
        compute='_total_cost',
        tracking=True,
        readonly=True
    )

    picking_type_name = fields.Char(
        string='Picking Type Name', related='picking_type_id.name')
    active = fields.Boolean('Active', default=True)
    man_confirm = fields.Boolean(
        'Manager Confirmation', tracking=True)
    client_id = fields.Many2one(
        'res.partner', string='Client', index=True, ondelete='cascade', required=False)

    def unlink(self):
        for picking in self:
            store_request_picking_type = self.env.ref(
                "topline.stock_picking_type_emp")
            if picking.picking_type_id == store_request_picking_type:
                raise UserError(
                    "You are not allowed to delete store requests, you may consider archiving instead!!!")
        return super(StockPicking, self).unlink()

    def button_submit(self):
        self.write({'state': 'submit'})
        for move in self.move_ids_without_package:
            move.state = 'submit'
        partner_ids = []
        if self.employee_id.parent_id.user_id:
            partner_ids.append(
                self.employee_id.parent_id.user_id.partner_id.id)
        colleagues = self.env['hr.employee'].sudo().search([('department_id', '=', self.department_id.id)])
        colleague_users = colleagues.mapped('user_id')
        partner_ids.extend(colleague_users.mapped('partner_id').ids)
        self.message_subscribe(partner_ids=partner_ids)
        subject = "Store request {} for {} needs approval".format(
            self.name, self.employee_id.name)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)
        return False

    def action_confirm2(self):
        self.action_confirm()
        self.write({'is_locked': True})
        for move in self.move_ids_without_package:
            move.state = 'confirmed'
        return True

    def button_validate2(self):
        return self.button_validate()

    def action_confirm(self):
        # self.write({'is_locked': True})
        # for move in self.move_ids_without_package:
        #     move.state = 'confirmed'
        res = super(StockPicking, self).action_confirm()
        if self.picking_type_id.name == 'Staff Store Requests':
            self.button_approve_srt()
            group_id = self.env.ref(
                'stock.group_stock_manager')
            user_ids = []
            partner_ids = []
            for user in group_id.users:
                user_ids.append(user.id)
                partner_ids.append(user.partner_id.id)
            self.message_subscribe(partner_ids=partner_ids)
            subject = "Store request {} has been authorized".format(self.name)
            self.message_post(subject=subject, body=subject,
                              partner_ids=partner_ids)
            return False
        return res

    def action_line_manager_approval(self):
        self.write({'state': 'approve'})
        group_id = self.env.ref(
            'topline.group_qa')
        for move in self.move_ids_without_package:
            move.state = 'approve'
        self.manager_confirm()
        subject = "Store request {} for {} has been approved by line manager".format(
            self.name, self.employee_id.name)
        partner_ids = []
        user_ids = []
        for user in group_id.users:
            user_ids.append(user.id)
            partner_ids.append(user.partner_id.id)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)

    def action_qa_qc_approval(self):
        self.write({'state': 'qa_qc_approve'})
        for move in self.move_ids_without_package:
            move.state = 'qa_qc_approve'
        self.manager_confirm()
        subject = "Store request {} for {} has been approved by QA/QC".format(
            self.name, self.employee_id.name)
        partner_ids = []
        for partner in self.message_partner_ids:
            partner_ids.append(partner.id)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)
        self.send_store_request_mail()

    def manager_confirm(self):
        for order in self:
            order.write({'man_confirm': True})
        return True

    @api.depends('move_ids_without_package.product_uom_qty')
    def _total_cost(self):
        for a in self:
            amt = 0
            for line in a.move_ids_without_package:
                if line.price_cost and line.product_uom_qty:
                    amt = line.price_cost * line.product_uom_qty
            a.total_cost += amt

    def button_reset(self):
        self.mapped('move_ids_without_package')._action_cancel()
        self.write({'state': 'draft'})
        return {}

    def send_store_request_mail(self):
        if self.picking_type_id.name == "Staff Store Requests" and self.state in ['draft', 'approve', 'waiting', 'confirmed']:
            group_id = self.env.ref(
                'stock.group_stock_manager')
            user_ids = []
            partner_ids = []
            for user in group_id.users:
                user_ids.append(user.id)
                partner_ids.append(user.partner_id.id)
            self.message_subscribe(partner_ids=partner_ids)
            subject = "Store request {} for {} needs Validation from Stock".format(
                self.name, self.employee_id.name)
            self.message_post(subject=subject, body=subject,
                              partner_ids=partner_ids)
            return False
        return True

    def send_store_request_done_mail(self):
        if self.state in ['done']:
            subject = "Store request '{}', for {} has been approved and validated".format(
                self.name, self.employee_id.name)
            partner_ids = []
            for partner in self.sheet_id.message_partner_ids:
                partner_ids.append(partner.id)
            self.sheet_id.message_post(
                subject=subject, body=subject, partner_ids=partner_ids)

    def button_reject(self):
        self.write({'state': 'reject'})
        subject = "Store request '{}', for {} has been rejected".format(
            self.name, self.employee_id.name)
        partner_ids = []
        for partner in self.message_partner_ids:
            partner_ids.append(partner.id)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)

    def button_approve_srt(self):
        self.need_approval = False
        return {}

    @api.depends('move_ids_without_package.price_unit')
    def _total_price(self):
        total_price = 0.0
        for rec in self:
            for line in rec.move_ids_without_package:
                total_price += line.price_subtotal
            rec.total_price = total_price

    def action_assign_owner(self):
        pass

    def create_atp_order(self):
        """
        Method to open create atp form
        """
        view_ref = self.env['ir.model.data'].check_object_reference(
            'topline_atp', 'topline_atp_form_view')
        view_id = view_ref[1] if view_ref else False

        for subscription in self:
            order_lines = []
            for line in subscription.move_ids_without_package:
                order_lines.append((0, 0, {
                    'name': line.product_id.name,
                    'product_id': line.product_id.id,
                    'qty': line.product_uom_qty,
                    'size': line.store_request_size,
                    'brand_id': line.brand_id.id,
                    'certificate_required': line.certificate_required,
                    'price': line.product_id.standard_price,
                }))

        res = {
            'type': 'ir.actions.act_window',
            'name': ('ATP FORM'),
            'res_model': 'atp.form',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': view_id,
            'target': 'current',
            'context': {'default_project_des': self.project_description, 'default_stock_source': self.name, 'default_expected_date': self.scheduled_date, 'default_atp_form_line_ids': order_lines}
        }
        return res

    def _notify_get_action_link(self, link_type, **kwargs):
        res = super()._notify_get_action_link(link_type, **kwargs)
        if self.picking_type_id == self.env.ref("topline_store_request.stock_picking_type_emp"):
            return self._get_record_url()
        return res

    def _get_record_url(self):
        base_url = self.get_base_url()
        params = {
            "id": self.id,
            "cids": self.id,
            "action": int(self.env.ref("topline_store_request.store_req_action_window")),
            "model": self._name,
            "menu_id": int(self.env.ref("topline_store_request.store_request")),
            "view_type": "form",
        }
        url = f"{base_url}/web#{urlencode(params)}"
        return url
