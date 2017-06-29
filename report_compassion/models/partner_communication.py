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

from .res_partner import IMG_DIR

from odoo import api, models, fields


class PartnerCommunication(models.Model):
    """ Add fields for retrieving values for communications.
    Send a communication when a major revision is received.
    """
    _inherit = 'partner.communication.job'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    product_id = fields.Many2one('product.product', 'Attach payment slip for')
    compassion_logo = fields.Binary(compute='_compute_compassion_logo')
    compassion_square = fields.Binary(compute='_compute_compassion_logo')

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    @api.multi
    def _compute_compassion_logo(self):
        with open(IMG_DIR + '/compassion_logo.png') as logo:
            with open(IMG_DIR + '/bluesquare.png') as square:
                data_logo = base64.b64encode(logo.read())
                data_square = base64.b64encode(square.read())
                for communication in self:
                    communication.compassion_logo = data_logo
                    communication.compassion_square = data_square

    @api.model
    def create(self, vals):
        """
        Fetch a success story at creation
        :param vals: values for record creation
        :return: partner.communication.job record
        """
        job = super(PartnerCommunication, self).create(vals)
        job.set_success_story()
        return job

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    @api.multi
    def send(self):
        """
        Change the report for communications to print with BVR
        Update the count of succes story prints when sending a receipt.
        :return: True
        """
        print_bvr = self.filtered(lambda j: j.send_mode == 'physical' and
                                  j.product_id)
        print_bvr.write({'report_id': self.env.ref(
            'report_compassion.report_a4_bvr').id})
        return super(PartnerCommunication, self).send()
