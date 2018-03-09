# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import api, models, fields


class PartnerCommunication(models.Model):
    """ Add fields for retrieving values for communications.
    Send a communication when a major revision is received.
    """
    _inherit = 'partner.communication.job'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    product_id = fields.Many2one('product.product', 'A4 + payment slip')
    preprinted = fields.Boolean(
        help='Enable if you print on a payment slip that already has company '
             'information printed on it.'
    )
    omr_enable_marks = fields.Boolean(string="Enable OMR",
        help='If set to True, the OMR marks are displayed in the '
             'communication.'
    )
    omr_should_close_envelope = fields.Boolean(string="OMR should close the "
        "envelope", help='If set to True, the OMR mark for closing the "'
        "envelope is added to the communication."
    )
    display_pp = fields.Boolean(string="Display PP",
        help="If not set, the PP is not printed upper the address."
    )

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
