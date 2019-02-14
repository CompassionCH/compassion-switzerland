# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Maxime Beck
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models, tools

testing = tools.config.get('test_enable')

if not testing:
    # prevent these forms to be registered when running tests

    class PartnerMatchform(models.AbstractModel):

        _inherit = 'cms.form.match.partner'

        def form_before_create_or_update(self, values, extra_values):
            """
            Avoid updating partner at GMC, use context to prevent this.
            """
            super(
                PartnerMatchform,
                self.with_context(no_upsert=True)
            ).form_before_create_or_update(values, extra_values)

        def after_partner_match(self, partner, new_partner, partner_vals,
                                values, extra_values):
            """
            Activate partner if it was a linked contact.
            :param partner: res.partner record matched
            :param new_partner: True if a new partner was created
            :param partner_vals: partner vals extracted from form
            :param values: form main object values
            :param extra_values: extra form values
            :return: None
            """
            if partner.contact_type == 'attached':
                if partner.type == 'email_alias':
                    # In this case we want to link to the main partner
                    partner = partner.contact_id
                    # Don't update e-mail address of main partner
                    del partner_vals['email']
                else:
                    # We unarchive the partner to make it visible
                    partner_vals.update({
                        'active': True,
                        'contact_id': False
                    })
            if new_partner:
                # Mark the partner to be validated
                partner_vals['state'] = 'pending'
            super(PartnerMatchform, self).after_partner_match(
                partner, new_partner, partner_vals, values, extra_values
            )
