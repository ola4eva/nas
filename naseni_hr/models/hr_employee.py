# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api
from odoo.addons.naseni_hr.utils.main import (
    has_three_months_to_retirement,
)

_logger = logging.getLogger(__name__)


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    institute_id = fields.Many2one(
        comodel_name="naseni_hr.institute", string="Institute"
    )
    pfa_id = fields.Many2one(comodel_name="naseni_hr.pfa", string="PFA")
    pension_pin = fields.Char("Pension PIN")
    date_join = fields.Date("Date Joined")

    @api.model
    def process_retirment_notification(self):
        retiring_employees = self.search([]).filtered(
            lambda emp: has_three_months_to_retirement(emp.birthday, emp.date_join)
        )
        _logger.info(f"Employees to retire are: {retiring_employees.mapped('name')}")
        # TODO: Create an email template to send a notification to the concerned party.
        self.send_retirement_notification_to_responsible(retiring_employees)
        return True

    @api.model
    def send_retirement_notification_to_responsible(self, retiring_employees=None):
        """Send notification email to responsible users.

        :param proposed_period: the proposed_period time for the retiring_employee
        :param customers: list of customers
        :return: None
        """
        # TODO: create a new group for the retirement reminders
        notification_group = self.env.ref("naseni_hr.group_employee_retirement")
        recipients = [partner.email_formatted for partner in notification_group.users.mapped("partner_id")]
        user = self.env.ref("base.user_admin")
        if retiring_employees is None:
            return False
        # config parameters
        sender = self.env.user.company_id.partner_id.email_formatted
        sender_dict = self.default_get(["reminder_name", "reminder_email"])
        reminder_name = self.env["res.config.settings"].get_values()[
            "employee_retirement_reminder_name"
        ]
        reminder_email = self.env["res.config.settings"].get_values()[
            "employee_retirement_reminder_email"]
        if sender_dict:
            sender = (
                reminder_name
                + " <"
                + reminder_email
                + ">"
            )
        if not sender:
            _logger.warning("No sender email configured in system parameters")
            return
        Mail = self.env["mail.mail"].sudo()
        retiring_employee_table = ""
        for num, retiring_employee in enumerate(retiring_employees, start=1):
            retiring_employee_table += (
                "<tr>"
                "<td style='border: 1px solid #96D4D4;'>"
                + str(num)
                + "</td><td style='border: 1px solid #96D4D4;'>"
                + retiring_employee.name
                + "</td><td style='border: 1px solid #96D4D4;'>"
                + retiring_employee.work_email
                or "" + "</td></tr>"
            )
        values = {
            "subject": "Employees Due for Retirement in 3 Months",
            "body_html": f"""
            <p>Employees retiring in 3 months</p>
            <p>
            Please be informed that the following employees are due to retire in 3 months.</p>
            <table style="border: 1px solid #96D4D4; border-collapse:collapse;" class="table table-bordered">
                <thead>
                    <tr>
                        <th style="border: 1px solid #96D4D4;">S/N</th>
                        <th style="border: 1px solid #96D4D4;">Name</th>
                        <th style="border: 1px solid #96D4D4;">Email</th>
                    </tr>
                </thead>
                <tbody style="border: 1px solid #96D4D4;">{retiring_employee_table}</tbody>
            </table>
            <p>Regards</p>
            <p>Naseni</p>
            """,
            "email_from": sender,
            "email_to": ",".join(recipients),
            "author_id": user.partner_id.id,
            "message_type": "user_notification",
        }
        _logger.info(f"{user.name} {user.partner_id.name}")
        try:
            Mail.with_context(user=user).create(values).sudo().send()
        except Exception as e:
            _logger.error(e)
        return True
