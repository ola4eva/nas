# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import models, fields


class AnalyticMixin(models.AbstractModel):
    _inherit = "analytic.mixin"

    analytic_distribution = fields.Json(
        string="Votebook",
    )
