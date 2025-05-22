from datetime import datetime
from odoo import models, fields, api

GROUP_CHECKER = "naseni_base.group_voucher_checker"
GROUP_AUDIT = "naseni_base.group_voucher_audit"
TEMPLATE_PREPARER = "naseni_payment_voucher.preparer_notification_template"
TEMPLATE_CHECKER = "naseni_payment_voucher.checker_notification_template"
TEMPLATE_AUDIT = "naseni_payment_voucher.audit_notification_template"


class AccountMove(models.Model):
    _inherit = "account.move"

    state = fields.Selection(
        selection_add=[
            ("submit", "Submitted"),
            ("checked", "Checked"),
            ("audit", "Audit"),
            ("posted",),
        ],
        ondelete={
            "submit": "set default",
            "checked": "set default",
            "audit": "set default",
        },
    )
    name = fields.Char(
        string="Number",
        # compute="_compute_name",
        # inverse="_inverse_name",
        inverse=False,
        compute=False,
        readonly=False,
        store=True,
        copy=False,
        tracking=True,
        index="trigram",
    )
    preparer_id = fields.Many2one(comodel_name="res.users", string="Prepared By")
    prepared_on = fields.Datetime(string="Prepared On")
    checker_id = fields.Many2one(comodel_name="res.users", string="Checked By")
    checked_on = fields.Datetime(string="Checked On")
    auditor_id = fields.Many2one(comodel_name="res.users", string="Audited By")
    audited_on = fields.Datetime(string="Audited On")
    date_confirmed = fields.Date("Confirmation Date")

    def unlink(self):
        """Override the unlink method to prevent deletion of records in certain states."""
        for record in self:
            if record.state != "draft":
                raise models.ValidationError(
                    "You cannot delete a record that is not in draft, submitted, checked or audit state."
                )
        return super(AccountMove, self).unlink()

    @api.depends("date", "auto_post")
    def _compute_hide_post_button(self):
        for record in self:
            record.hide_post_button = (
                record.state not in ("draft", "submit", "checked", "audit")
                or record.auto_post != "no"
                and record.date > fields.Date.context_today(record)
            )

    def action_submit(self):
        """Submit to HOD."""
        self.ensure_one()

        # Get the employee's HOD
        def get_employee_hod(employee_id=None):
            """Get the HOD of the provided employee"""
            if not employee_id:
                return None
            employee_id.department_id and employee_id.department_id.manager_id or employee_id.parent_id

        # Notify the checker
        employee_id = self.env["hr.employee"].search(
            [("user_id", "=", self.env.uid)], limit=1
        )
        HOD = get_employee_hod(employee_id)
        self.send_notification(
            user_ids=[HOD and HOD.id or 0], template_id=TEMPLATE_CHECKER
        )

        return self.write(
            {
                "preparer_id": self.env.uid,
                "prepared_on": fields.Datetime.now(),
                "name": self.env["ir.sequence"].next_by_code("payment.voucher"),
                "state": "submit",
            }
        )

    def action_checked(self):
        """Perform Checking..."""
        self.ensure_one()

        # Notify the auditor
        audit_group = self.env.ref(GROUP_AUDIT)
        self.send_notification(group_ids=audit_group.ids, template_id=TEMPLATE_AUDIT)

        return self.write(
            {
                "checker_id": self.env.uid,
                "checked_on": fields.Datetime.now(),
                "state": "checked",
            }
        )

    def action_audit(self):
        """Perfrom auditing."""
        self.ensure_one()
        # Notify the initiator
        self.send_notification([self.preparer_id.id], template_id=TEMPLATE_PREPARER)
        return self.write(
            {
                "audited_on": fields.Datetime.now(),
                "auditor_id": self.env.uid,
                "state": "audit",
            }
        )

    def send_notification(self, user_ids=None, group_ids=None, template_id=None):
        """Send notification to the groups that need to be informed

        Parameters
        ----------
        user_ids list:
            ids of the users to be notified. Mutually exclusive of the group_ids
        group_ids list:
            ids of the groups to be notified. Mutually exclusive of the user_ids
        template_id str:
            external identifier of the email templat to be used.

        """
        self.ensure_one()
        if not (user_ids or group_ids) or not template_id:
            return False
        template = self.env.ref(template_id)
        if group_ids:
            groups = self.env["res.groups"].browse(group_ids)
            users = groups.mapped("users")
        else:
            users = self.env["res.users"].browse(user_ids)
        return template.with_context(recipients=users).send_mail(
            self.id, force_send=True
        )

    def action_post(self):
        super(AccountMove, self).action_post()
        self.date_confirmed = fields.Date.today()

    def _get_default_voucher_report_name(self):
        for record in self:
            month = (
                record.invoice_date.strftime("%B")
                if record.invoice_date
                else datetime.now().strftime("%B")
            )
            year = (
                record.invoice_date.year if record.invoice_date else datetime.now().year
            )
            return f"Payment Voucher - {record.name or ''} - {record.partner_id.name or ''} - {month} - {year}"
