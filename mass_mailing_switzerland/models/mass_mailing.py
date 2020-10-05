##############################################################################
#
#    Copyright (C) 2016-2017 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import api, models, fields, _
from odoo.exceptions import UserError


class MassMailing(models.Model):
    _inherit = "mail.mass_mailing"

    internal_name = fields.Char("Internal Variant Name")

    # Default values
    mailing_model_id = fields.Many2one(default=lambda s: s.env.ref(
        'base.model_res_partner').id)
    enable_unsubscribe = fields.Boolean(default=True)
    unsubscribe_tag = fields.Char(default="[unsub]")
    mailchimp_country_filter = fields.Char(
        compute="_compute_has_mailchimp_filter")
    mailchimp_donation_filter = fields.Char(
        compute="_compute_has_mailchimp_filter"
    )

    @api.multi
    def _compute_has_mailchimp_filter(self):
        country_name = False
        fund_name = False
        country_filter_id = self.env["res.config.settings"].get_param(
            "mass_mailing_country_filter_id")
        if country_filter_id:
            country_name = self.env[
                "compassion.field.office"].browse(country_filter_id).name
        fund_id = self.env["res.config.settings"].get_param(
            "mass_mailing_donation_fund_id")
        if fund_id:
            fund_name = self.env["product.template"].sudo().browse(fund_id).name
        for mailing in self:
            mailing.mailchimp_country_filter = country_name
            mailing.mailchimp_donation_filter = fund_name

    @api.multi
    def name_get(self):
        res = []
        for mass_mail in self:
            _id, _name = super(MassMailing, mass_mail).name_get()[0]
            if mass_mail.internal_name:
                res.append((_id, f"{_name} [{mass_mail.internal_name}]"))
            else:
                res.append((_id, _name))
        return res

    @api.onchange('mailing_model_id', 'contact_list_ids')
    def _onchange_model_and_list(self):
        if self.mailing_model_name == 'res.partner':
            mailing_domain = repr([
                ('customer', '=', True),
                ('opt_out', '=', False),
                ('email', '!=', False)
            ])
        else:
            mailing_domain = super()._onchange_model_and_list()
        self.mailing_domain = mailing_domain

    def send_now_mailchimp(self, account=False):
        queue_job = self.env["queue.job"].search([
            ("channel", "=", "root.mass_mailing_switzerland.update_mailchimp"),
            ("state", "!=", "done")
        ], limit=1)
        if queue_job:
            raise UserError(_(
                "Mailchimp is updating its MERGE FIELDS right now. "
                "You should wait for the process to finish before sending the mailing."
            ))
        return super().send_now_mailchimp(account)
