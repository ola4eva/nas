from . import models
from odoo import SUPERUSER_ID, api, fields

from datetime import datetime, timedelta


def pre_init_hook(env):
    env = api.Environment(env.cr, SUPERUSER_ID, {})

    cron = env.ref("mail.ir_cron_module_update_notification", raise_if_not_found=False)
    if cron:
        cron.write({"active": False})
        domain = [
            ("model", "=", "ir.cron"),
            ("module", "=", "mail"),
            ("res_id", "=", cron.id),
        ]
        data = env["ir.model.data"].with_user(SUPERUSER_ID).search(domain, limit=1)
        data.write({"noupdate": False})


def post_init_hook(env):
    datetime = "%s" % (fields.Datetime.now() + timedelta(days=1825),)
    env = api.Environment(env.cr, SUPERUSER_ID, {})
    config = (
        env["ir.config_parameter"]
        .with_user(SUPERUSER_ID)
        .set_param("database.expiration_date", datetime)
    )
    cron = env.ref("mail.ir_cron_module_update_notification", raise_if_not_found=False)
    if cron:
        domain = [
            ("model", "=", "ir.cron"),
            ("module", "=", "mail"),
            ("res_id", "=", cron.id),
        ]
        data = env["ir.model.data"].with_user(SUPERUSER_ID).search(domain, limit=1)
        data.write({"noupdate": True})
