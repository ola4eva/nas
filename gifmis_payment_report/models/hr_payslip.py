from odoo import models

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    def action_generate_gifmis_report(self):
        return {
            'name': 'Generate GIFMIS Report',
            'type': 'ir.actions.act_window',
            'res_model': 'gifmis.report.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_payslip_ids': [(6, 0, self.ids)],
            }
        }
