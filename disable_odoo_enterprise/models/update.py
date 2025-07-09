from datetime import timedelta
from odoo import models, fields


class PublisherWarrantyContract(models.AbstractModel):
    _inherit = "publisher_warranty.contract"

    def update_notification(self, cron_mode=True, length=None):
        """Disable update notification to Odoo"""
        get_param = self.env["ir.config_parameter"].sudo().get_param
        database_expiration_date = fields.Datetime.from_string(
            get_param("database.expiration_date")
        )
        if (database_expiration_date - fields.Datetime.now()).days > 7:
            self.extend_database_expiration(length)
        return True

    def extend_database_expiration(self, length=365):
        today = fields.Datetime.now()
        new_expiration_date = today + timedelta(days=length)
        set_param = self.env["ir.config_parameter"].sudo().set_param
        # Update expiration date
        set_param(
            "database.expiration_date", fields.Datetime.to_string(new_expiration_date)
        )
