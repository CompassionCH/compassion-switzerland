# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2017-2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models, api


class SendgridSubstitution(models.Model):
    _inherit = 'sendgrid.substitution'

    @api.multi
    def replace_tracking_link(self, campaign_id=False, medium_id=False,
                              source_id=False):
        """
        Takes special {wp/page} keywords and automatically creates a
        tracked URL for replacement.
        :param campaign_id: utm.campaign id
        :param medium_id:   utm.medium id
        :param source_id:   utm.source id
        :return: True
        """
        wp_url = self.env['wordpress.configuration'].get_host()
        for substitution in self.filtered(lambda s: '{wp' in s.key):
            page_path = substitution.key.replace('{wp', '').replace('}', '')
            page_url = '{}{}'.format(wp_url, page_path)
            link_tracker = self.env['link.tracker'].sudo().create({
                'url': page_url,
                'campaign_id': campaign_id,
                'medium_id': medium_id,
                'source_id': source_id
            })
            substitution.value = link_tracker.short_url.split('//')[1]
        return True
