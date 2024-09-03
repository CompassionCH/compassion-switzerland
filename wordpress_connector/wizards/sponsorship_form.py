##############################################################################
#
#    Copyright (C) 2023 Compassion CH (http://www.compassion.ch)
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging

from odoo import _, api, models

_logger = logging.getLogger(__name__)


class WebsiteSponsorship(models.TransientModel):
    _inherit = "cms.form.sponsorship"

    @api.model_create_multi
    def create(self, vals_list):
        # Notify SDS staff when new sponsorship is made
        records = super().create(vals_list)
        for form, vals in zip(records, vals_list):
            if form.match_update:
                # This is step2 when martch_update is True, we don't need to notify staff
                continue
            web_info = ""
            for key, value in vals.items():
                web_info += "<li>" + key + ": " + str(value or "") + "</li>"
            sponsor_lang = form.partner_id.lang[:2]
            staff_param = "sponsorship_" + sponsor_lang + "_id"
            staff = self.env["res.config.settings"].sudo().get_param(staff_param)
            notify_text = (
                "A new sponsorship was made on the website. Please "
                "verify all information and validate the sponsorship "
                "on Odoo: <br/><br/><ul>"
            ) + web_info

            title = _("New sponsorship from the website")
            form.contract_id.sudo().message_post(
                body=notify_text,
                subject=title,
                partner_ids=[staff],
                subtype_xmlid="mail.mt_comment",
                content_subtype="html",
            )
        return records
