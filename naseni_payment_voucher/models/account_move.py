from odoo import models, fields, api

GROUP_CHECKER = "naseni_payment_voucher.group_voucher_checker"
GROUP_AUDIT = "naseni_payment_voucher.group_voucher_audit"
TEMPLATE_PREPARER = "naseni_payment_voucher.preparer_notification_template"
TEMPLATE_CHECKER = "naseni_payment_voucher.checker_notification_template"
TEMPLATE_AUDIT = "naseni_payment_voucher.audit_notification_template"
class AccountMove(models.Model):
    _inherit = "account.move"

    state = fields.Selection(selection_add=[
        ('submit', "Submitted"),
        ('checked', "Checked"),
        ('audit', "Audit"),
        ('posted',)
    ],
    ondelete={
        'submit': 'set default',
        'checked': 'set default',
        'audit': 'set default',
        } 
    )
    preparer_id = fields.Many2one(comodel_name='res.users', string='Prepared By')
    prepared_on = fields.Datetime(string='Prepared On')
    checker_id = fields.Many2one(comodel_name='res.users', string='Checked By')
    checked_on = fields.Datetime(string='Checked On')
    auditor_id = fields.Many2one(comodel_name='res.users', string='Audited By')
    audited_on = fields.Datetime(string='Audited On')
    date_confirmed = fields.Date('Confirmation Date')

    @api.depends('date', 'auto_post')
    def _compute_hide_post_button(self):
        for record in self:
            record.hide_post_button = record.state not in ('draft', 'submit', "checked", 'audit') \
                or record.auto_post != 'no' and record.date > fields.Date.context_today(record)

    def action_submit(self):
        """Submit to HOD."""
        self.ensure_one()

        # Get the employee's HOD
        def get_employee_hod(employee_id=None):
            """Get the HOD of the provided employee"""
            if not employee_id:
                return None
            employee_id.department_id and employee_id.department_id.manager_id \
                or employee_id.parent_id

        # Notify the checker
        employee_id = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        get_employee_hod
        HOD = get_employee_hod(employee_id)
        # TODO: get the hod user id
        self.send_notification(user_ids=[HOD and HOD.id or 0], template_id=TEMPLATE_CHECKER)
        return self.write({
            "preparer_id": self.env.uid,
            "prepared_on": fields.Datetime.now(),
            "state": "submit"
        })

    def action_checked(self):
        """Perform Checking..."""
        self.ensure_one()
        # Notify the auditor
        audit_group = self.env.ref(GROUP_AUDIT)

        self.send_notification(group_ids=audit_group.ids, template_id=TEMPLATE_AUDIT)
        return self.write({
            "checker_id": self.env.uid,
            "checked_on": fields.Datetime.now(),
            "state": "checked"
        })

    def action_audit(self):
        """Perfrom auditing."""
        self.ensure_one()
        # Notify the initiator
        self.send_notification([self.preparer_id.id], template_id=TEMPLATE_PREPARER)
        return self.write({
            "audited_on": fields.Datetime.now(),
            "auditor_id": self.env.uid,
            "state": "audit"
        })

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
            groups = self.env['res.groups'].browse(group_ids)
            users = groups.mapped("users")
        else:
            users = self.env['res.users'].browse(user_ids)
        return template.with_context(recipients=users).send_mail(self.id, force_send=True)

    def action_post(self):
        super(AccountMove, self).action_post()
        self.date_confirmed = fields.Date.today()
