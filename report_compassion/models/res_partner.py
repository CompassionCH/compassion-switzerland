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

from odoo import api, models, fields


IMG_DIR = os.path.dirname(os.path.realpath(__file__)) + '/../static/img/'


class ResPartner(models.Model):
    """ Add fields for retrieving values for communications.
    """
    _inherit = 'res.partner'

    sub_proposal_form = fields.Binary(compute='_compute_sub_form')
    bvr_background = fields.Binary(compute='_compute_bvr_background')

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
