# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################
import base64
import os
import re

from openerp import api, models, fields


IMG_DIR = os.path.dirname(os.path.realpath(__file__)) + '/../static/img/'


class ResPartner(models.Model):
    """ Add fields for retrieving values for communications.

    - Short address
        Mr. John Doe
        Street
        City
        Country
    """
    _inherit = 'res.partner'

    short_address = fields.Char(compute='_compute_address')
    sub_proposal_form = fields.Binary(compute='_compute_sub_form')
    bvr_background = fields.Binary(compute='_compute_bvr_background')

    @api.multi
    def _compute_address(self):
        # Replace line returns
        p = re.compile('\\n+')
        for partner in self:
            t_partner = partner.with_context(lang=partner.lang)
            if not partner.is_company:
                res = t_partner.title.shortcut + ' '
                if partner.firstname:
                    res += partner.firstname + ' '
                res += partner.lastname + '<br/>'
            else:
                res = partner.name + '<br/>'
            res += t_partner.contact_address
            partner.short_address = p.sub('<br/>', res)

    @api.multi
    def _compute_sub_form(self):
        for partner in self:
            fname = IMG_DIR + 'SUB_form_{}.jpg'.format(partner.lang)
            with open(fname) as form_image:
                partner.sub_proposal_form = base64.b64encode(form_image.read())

    @api.multi
    def _compute_bvr_background(self):
        with open(IMG_DIR + '/bvr.jpg') as bgf:
            data = base64.b64encode(bgf.read())
            for partner in self:
                partner.bvr_background = data
