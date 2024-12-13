from odoo import models, fields, api
from dateutil.relativedelta import relativedelta

class Employee(models.Model):
    _inherit = 'hr.employee'

    # Fields from the screenshot
    join_date = fields.Date(string="Join Date")
    next_anniversary_date = fields.Date(string="Next Anniversary Date", compute="_compute_anniversary_dates", store=True)
    anniversary_notify_date = fields.Date(string="Anniversary Notify Date", compute="_compute_anniversary_dates", store=True)
    probation_period_days = fields.Integer(string="Probation Period (Days)")
    confirmation_date = fields.Date(string="Confirmation Date")
    confirmation_period = fields.Integer(string="Confirmation Period")
    confirmed = fields.Boolean(string="Confirmed", default=False)
    car_allowance_date = fields.Date(string="Car Allowance Date")
    full_13th_month = fields.Boolean(string="Full 13th Month")
    notification_date = fields.Date(string="Notification Date")
    left_date = fields.Date(string="Left Date")
    reason_for_leaving = fields.Text(string="Reason for Leaving")

    NOD = fields.Integer(string="Number of Day's Worked", default=0)
    misc_notes = fields.Text(string="Miscellaneous Notes")

    # Compute next anniversary and notify dates
    @api.depends('join_date')
    def _compute_anniversary_dates(self):
        for record in self:
            if record.join_date:
                record.next_anniversary_date = record.join_date + relativedelta(years=1)
                record.anniversary_notify_date = record.next_anniversary_date - relativedelta(days=30)
            else:
                record.next_anniversary_date = False
                record.anniversary_notify_date = False

    # Confirm employee action
    def action_confirm_employee(self):
        for record in self:
            record.confirmed = True
