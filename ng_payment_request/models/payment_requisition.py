from odoo import fields, models, api, _, exceptions
from odoo.fields import Command
from odoo.exceptions import UserError
import logging
from odoo.tools.misc import groupby


class payment_request(models.Model):
    _inherit = ["mail.thread"]
    _name = "payment.requisition"
    _description = "Cash Requisition"
    _order = "create_date desc"

    @api.depends(
        "request_line", "request_line.request_amount", "request_line.approved_amount"
    )
    def _compute_requested_amount(self):
        for record in self:
            requested_amount, approved_amount = 0, 0
            for line in record.request_line:
                requested_amount += line.request_amount
                approved_amount += line.approved_amount
            record.amount_company_currency = requested_amount
            record.requested_amount = requested_amount
            record.approved_amount = approved_amount
            company_currency = record.company_id.currency_id
            current_currency = record.currency_id
            if company_currency != current_currency:
                amount = company_currency.compute(requested_amount, current_currency)
                record.amount_company_currency = amount

    name = fields.Char("Name", default="/", copy=False)
    requester_id = fields.Many2one(
        "res.users", "Requester", required=True, default=lambda self: self.env.user
    )
    employee_id = fields.Many2one("hr.employee", "Employee", required=True)
    department_id = fields.Many2one("hr.department", "Department")
    date = fields.Date("Request Date", default=fields.Date.context_today)
    description = fields.Text("Description")
    request_line = fields.One2many(
        "payment.requisition.line", "payment_request_id", string="Lines", copy=False
    )
    requested_amount = fields.Float(
        compute="_compute_requested_amount",
        string="Requested Amount",
        store=True,
        copy=False,
    )
    approved_amount = fields.Float(
        compute="_compute_requested_amount",
        string="Approved Amount",
        store=True,
        copy=False,
    )
    amount_company_currency = fields.Float(
        compute="_compute_requested_amount",
        string="Amount In Company Currency",
        store=True,
        copy=False,
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        required=True,
        default=lambda self: self.env.user.company_id.currency_id.id,
    )
    company_id = fields.Many2one(
        "res.company",
        "Company",
        required=True,
        default=lambda self: self.env["res.company"]._company_default_get(
            "payment.requisition"
        ),
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("awaiting_approval", "Awaiting Department Approval"),
            ("mgr_approve", "Treasury To Approve"),
            ("gm_approve", "Financial Controller To Approve"),
            ("approved", "Approved"),
            ("paid", "Paid"),
            ("refused", "Refused"),
            ("cancelled", "Cancelled"),
        ],
        tracking=True,
        default="draft",
        string="State",
    )
    need_gm_approval = fields.Boolean(
        "Needs First Approval?", copy=False, readonly=True
    )
    need_md_approval = fields.Boolean(
        "Needs Final Approval?", copy=False, readonly=True
    )
    general_manager_id = fields.Many2one(
        "hr.employee", "General Manager", readonly=True
    )
    manging_director_id = fields.Many2one(
        "hr.employee", "Managing Director", readonly=True
    )
    dept_manager_id = fields.Many2one(
        "hr.employee", "Department Manager", readonly=True
    )
    dept_manager_approve_date = fields.Date(
        "Approved By Department Manager On", readonly=True
    )
    gm_approve_date = fields.Date("First Approved On", readonly=True)
    director_approve_date = fields.Date("Final Approved On", readonly=True)
    analytic_account_id = fields.Many2one(
        "account.analytic.account",
        string="Analytic Account",
        related="request_line.analytic_account_id",
        store=True,
    )
    bill_ids = fields.Many2many(
        "account.move",
        string="Vendor Bills",
        domain="[('move_type', '=', 'in_invoice')]",
        copy=False,
    )
    payment_state = fields.Selection(
        [
            ("not_paid", "Not Paid"),
            ("paid", "Paid"),
        ],
        compute="_compute_payment_state",
        default="not_paid",
        string="Payment State",
    )
    category_id = fields.Many2one(
        "payment.requisition.category",
        string="Category",
        related="request_line.category_id",
    )

    @api.model_create_multi
    def create(self, vals):
        for val in vals:
            if not val.get("name"):
                val["name"] = self.env["ir.sequence"].get("payment.requisition")
        return super().create(vals)

    def unlink(self):
        for record in self:
            if record.state != "draft":
                raise UserError("Only draft records can be deleted!")
        return super().unlink()

    def copy_data(self, default=None):
        if default is None:
            default = {}
        if "request_line" not in default:
            default["request_line"] = [
                Command.create(line.copy_data()[0]) for line in self.request_line
            ]
        return super().copy_data(default)

    @api.onchange("requester_id")
    def onchange_requester(self):
        employee = self.env["hr.employee"].search(
            [("user_id", "=", self._uid)], limit=1
        )
        self.employee_id = employee.id
        self.department_id = (
            employee.department_id and employee.department_id.id or False
        )

    def action_confirm(self):
        if not self.request_line:
            raise exceptions.UserError(
                _("Can not confirm request without request lines.")
            )

        if not self.department_id.manager_id:
            raise exceptions.UserError(
                _("Please contact HR to setup a manager for your department.")
            )
        body = _(
            "Dear %s, payment request %s has been submitted by %s for your approval."
            % (self.department_id.manager_id.name, self.name, self.env.user.name)
        )
        self.notify(
            body=body,
            users=[self.department_id.manager_id.user_id.partner_id.id],
            group=False,
        )
        users = (
            self.request_line.mapped("analytic_account_id")
            .mapped("user_ids")
            .mapped("partner_id")
            .ids
        )
        self.notify(
            body="A new payment request %s has been raised for your department"
            % (self.name),
            users=users,
            subscribe=True,
        )
        self.state = "awaiting_approval"
        return True

    def action_approve(self):
        for line in self.request_line:
            if line.approved_amount <= 0.0:
                raise exceptions.UserError(
                    _("Approved amount cannot be less then or equal to Zero.")
                )
        body = _("You have a request from %s to approve." % (self.employee_id.name))
        self.notify(body=body, users=[], group="ng_payment_request.general_manager")
        emp = self.env["hr.employee"].search([("user_id", "=", self._uid)], limit=1)
        self.update(
            {
                "dept_manager_id": emp.id,
                "state": "mgr_approve",
                "dept_manager_approve_date": fields.Date.context_today(self),
            }
        )
        return True

    def action_gm_approve(self):
        for line in self.request_line:
            if line.approved_amount <= 0.0:
                raise exceptions.UserError(
                    _("Approved amount cannot be less then or equal to Zero.")
                )
        self.need_md_approval = True
        body = _(
            "Payment request %s has been approved. Please provide final approval."
            % (self.name)
        )
        self.notify(body=body, group="ng_payment_request.managing_director")
        emp = self.env["hr.employee"].search([("user_id", "=", self._uid)], limit=1)
        self.update(
            {
                "state": "gm_approve",
                "general_manager_id": emp.id,
                "gm_approve_date": fields.Date.context_today(self),
            }
        )
        return True

    def _update_request_status(self):
        for record in self:
            if record.bill_ids and all(
                [state == "posted" for state in record.bill_ids.mapped("state")]
            ):
                emp = self.env["hr.employee"].search(
                    [("user_id", "=", self._uid)], limit=1
                )
                body = _(
                    "Payment request %s has been approved. Please proceed with the payment."
                    % (self.name)
                )
                self.notify(body=body, group="account.group_account_manager")
                record.update(
                    {
                        "director_approve_date": fields.Date.context_today(self),
                        "manging_director_id": emp.id,
                        "state": "approved",
                    }
                )

    def action_md_approve(self):
        """Create Vendor Bill"""
        vals_list = self._get_bill_create_values()
        vendor_bills = self.env["account.move"].sudo().create(vals_list)
        self.bill_ids += vendor_bills
        return self.write({"state": "approved"})

    def _get_bill_create_values(self):
        """Get the values to create the vendor bill with"""

        def _get_line_vals(line):
            return {
                "name": line.name,
                "account_id": line.expense_account_id.id,
                "quantity": 1,
                "price_unit": line.approved_amount,
                "analytic_distribution": {line.analytic_account_id.id: 100},
            }

        vals_list = []

        # Group the requisition lines by customer
        for partner, lines in groupby(self.request_line, key=lambda l: l.partner_id):
            values = dict()
            values["state"] = "draft"
            values["partner_id"] = partner.id
            values["invoice_date"] = fields.Date.today()
            values["move_type"] = "in_invoice"
            values["date"] = fields.Date.today()
            values["currency_id"] = self.currency_id.id
            values["invoice_line_ids"] = [
                Command.create(_get_line_vals(line)) for line in lines
            ]
            vals_list.append(values)
        return vals_list

    def action_view_bills(self):
        self = self.sudo()
        action = self.env.ref("account.action_move_in_invoice_type")
        result = action.read()[0]
        if len(self.bill_ids) == 1:
            res = self.env.ref("account.view_move_form", False)
            result["views"] = [(res and res.id or False, "form")]
            result["res_id"] = self.bill_ids.id
            return result
        result["domain"] = "[('id', 'in', " + str(self.bill_ids.ids) + ")]"
        return result

    def _compute_payment_state(self):
        """Compute Payment State"""
        for record in self:
            payment_state = "not_paid"
            if record.bill_ids and all(
                [bill.payment_state == "paid" for bill in record.bill_ids]
            ):
                payment_state = "paid"
            if record.state != "paid" and payment_state == "paid":
                record.state = "paid"
            record.payment_state = payment_state

    def notify(self, body="", users=[], group=False, subscribe=False):
        post_msg = []
        if group:
            users = self.env["res.users"].search(
                [
                    ("active", "=", True),
                    ("company_id", "=", self.env.user.company_id.id),
                ]
            )
            for user in users:
                if user.sudo().has_group(group) and user.id != 1:
                    post_msg.append(user.partner_id.id)
        else:
            post_msg = users
        if len(post_msg):
            self.message_post(body=body, partner_ids=post_msg)
            if subscribe:
                self.message_subscribe(post_msg)
        return True

    def action_pay(self):
        for record in self:
            if record.bill_ids and all(
                [bill.state == "paid" for bill in record.bill_ids]
            ):
                record.write({"state": "paid"})
        return True

    def action_cancel(self):
        self.state = "cancelled"
        return True

    def action_reset(self):
        self.state = "draft"
        return True

    def action_refuse(self):
        self.state = "refused"
        return True

    def payment_method(self, payment_type):
        return self.env["account.payment.method"].search(
            [("code", "=", "manual"), ("payment_type", "=", payment_type)], limit=1
        )


class payment_request_line(models.Model):
    _name = "payment.requisition.line"
    _description = "Cash Requisition Line"

    name = fields.Char(
        "Description",
        required=True,
    )
    request_amount = fields.Float(
        "Requested Amount",
        required=True,
    )
    approved_amount = fields.Float("Approved Amount")
    payment_request_id = fields.Many2one(
        "payment.requisition", string="Payment Request"
    )
    expense_account_id = fields.Many2one("account.account", "Account")
    analytic_account_id = fields.Many2one(
        "account.analytic.account", string="Analytic Account", required=True
    )
    credit_account_id = fields.Many2one(
        comodel_name="account.account", string="Pay From"
    )
    state = fields.Selection(string="State", related="payment_request_id.state")
    partner_id = fields.Many2one("res.partner", string="Customer/Vendor")
    category_id = fields.Many2one(
        "payment.requisition.category",
        string="Category",
        required=True,
    )

    def unlink(self):
        if self.state != "draft":
            raise UserError("Only draft records can be deleted!")
        return super().unlink()

    @api.onchange("request_amount")
    def _get_request_amount(self):
        if self.request_amount:
            amount = self.request_amount
            self.approved_amount = amount
