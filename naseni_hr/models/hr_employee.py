# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api
from odoo.addons.naseni_hr.utils.main import has_three_months_to_retirement

_logger = logging.getLogger(__name__)


class HrEmployeeBase(models.AbstractModel):
    _inherit = "hr.employee.base"
    _sql_constraints = [
        (
            "name_uniq",
            "UNIQUE (staff_id)",
            "You can not have two employees with the same Staff Number !",
        )
    ]

    def _valid_field_parameter(self, field, name):
        return name == "tracking" or super()._valid_field_parameter(field, name)

    institute_id = fields.Many2one(
        comodel_name="naseni_hr.institute", string="Center"
    )
    pfa_id = fields.Many2one(comodel_name="naseni_hr.pfa", string="PFA(*)", required=True)
    pension_pin = fields.Char("Pension PIN(*)", required=True)
    date_appointment = fields.Date("Date of First Appointment")
    date_confirm = fields.Date("Date of Confirmation")
    date_present = fields.Date("Date of Present Appointment")
    date_join = fields.Date("Joined Date")
    staff_id = fields.Char("Staff ID(*)", required=True)
    employee_no = fields.Char("IPPIS No.(*)", required=True)
    dir_id = fields.Many2one(comodel_name="naseni_hr.directorate", string="Directorate")
    cadre_id = fields.Many2one(comodel_name="naseni_hr.cadre", string="Cadre")
    state_id = fields.Many2one("res.country.state", string="State")
    lga_id = fields.Many2one(
        "res.country.state.lga", string="Lga", domain="[('state_id', '=', state_id)]"
    )
    geo = fields.Selection(
        [
            ("nw", "NORTH WEST"),
            ("ne", "NORTH EAST"),
            ("nc", "NORTH CENTRAL"),
            ("sw", "SOUTH WEST"),
            ("se", "SOUTH EAST"),
            ("ss", "SOUTH SOUTH"),
        ],
        groups="hr.group_hr_user",
        tracking=True,
        string="Geo Political Zone",
    )
    acc_qual = fields.Char("Academic Qualification")
    prof_qual = fields.Char("Professional Qualification")
    tin = fields.Char("Tax ID No.(*)", required=True)
    nhf = fields.Char("National Housing Fund")
    nin = fields.Char("National ID No.")
    title_id = fields.Many2one(comodel_name="res.partner.title", string="Title")
    next_of_kin_ids = fields.One2many('naseni_hr.next_of_kin', 'employee_id', string='Next of Kin')
    trade_union = fields.Char('Trade Union')

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
        recipients = [
            partner.email_formatted
            for partner in notification_group.users.mapped("partner_id")
        ]
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
            "employee_retirement_reminder_email"
        ]
        if sender_dict:
            sender = reminder_name + " <" + reminder_email + ">"
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
