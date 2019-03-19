# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Christopher Meier <dev@c-meier.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import yaml
import logging

from odoo import api, fields, models
from odoo.tools import html2plaintext

_logger = logging.getLogger(__name__)


class CrmWordpressRequest(models.Model):
    _inherit = "crm.claim"

    front_matter = fields.Text()

    # -------------------------------------------------------
    # Mail gateway
    # -------------------------------------------------------

    # Parse the new message to check if it comes from Wordpress and if so parse
    # it and fill the new object.
    @api.multi
    def message_new(self, msg, custom_values=None):
        if custom_values is None:
            custom_values = {}
        defaults = {}

        # Read YAML front matter
        yaml_delim = '---' + '\n'
        desc = html2plaintext(msg.get('body')) if msg.get('body') else ''
        if desc.startswith(yaml_delim):
            parts = desc[len(yaml_delim):].split('\n' + yaml_delim, 1)

            if len(parts) == 2:  # Does contain a front matter.
                defaults['front_matter'] = parts[0]
                desc = parts[1]
                try:
                    front_matter = yaml.load(parts[0])
                except yaml.YAMLError:
                    _logger.warning("Could not parse the front matter.",
                                    exc_info=True)
                else:
                    self._parse_front_matter(front_matter, defaults)
            defaults['description'] = u'<pre>{}</pre>'.format(desc)

        defaults.update(custom_values)

        return super(CrmWordpressRequest, self).message_new(
            msg, custom_values=defaults)

    def _parse_front_matter(self, fm, values):
        # Match the partner
        match_obj = self.env['res.partner.match.wp']

        if 'title' in fm:
            fm['title'] = match_obj.match_title(fm['title'])

        if 'lang' in fm:
            fm['lang'] = match_obj.match_lang(fm['lang'])

        partner = match_obj.match_partner_to_infos(fm)
        values['partner_id'] = partner.id

        # Match claim type
        if 'claim_type' in fm:
            type_name = fm['claim_type']
            type_obj = self.env['crm.claim.type']
            ct = type_obj.search([('name', '=ilike', type_name)],
                                 limit=1)
            if ct:
                values['claim_type'] = ct.id
