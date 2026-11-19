from odoo import models


class ResPartner(models.Model):
    _inherit = "res.partner"

    def _compute_im_status(self):
        # hr_holidays_public reads user_ids.employee_id without sudo, which fails
        # for portal users (e.g. presence update on survey submit).
        return super(ResPartner, self.sudo())._compute_im_status()
