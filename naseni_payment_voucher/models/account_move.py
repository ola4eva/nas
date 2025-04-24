from odoo import models, fields, api


class AccountMove(models.Model):
    _inherit = "account.move"

    state = fields.Selection(selection_add=[
        ('submit', "Submitted"),
        ('checking', "To Check"),
        ('audit', "Audit"),
        ('posted',)
    ],
    ondelete={
        'submit': 'set default',
        'checking': 'set default',
        'audit': 'set default',
        } 
    )

    @api.depends('date', 'auto_post')
    def _compute_hide_post_button(self):
        for record in self:
            record.hide_post_button = record.state not in ('draft', 'submit', "checking", 'audit') \
                or record.auto_post != 'no' and record.date > fields.Date.context_today(record)

    def action_submit(self):
        """Submit to HOD."""
        self.state = "submit"

    def action_checking(self):
        """Perform Checking..."""
        self.state = "checking"

    def action_audit(self):
        """Perfrom auditing."""
        self.state = "audit"