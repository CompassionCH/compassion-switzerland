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


class MassMailing(models.Model):
    _inherit = "mail.mass_mailing"

    internal_name = fields.Char("Internal Variant Name")

    # Default values
    mailing_model_id = fields.Many2one(default=lambda s: s.env.ref(
        'base.model_res_partner').id)
    enable_unsubscribe = fields.Boolean(default=True)
    unsubscribe_tag = fields.Char(default="[unsub]")

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
