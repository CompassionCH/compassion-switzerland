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
    display_pp = fields.Boolean(
        string='Display PP',
        help='If not set, the PP is not printed upper the address.',
        default=True
    )

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
        return super().send()

    @api.model
    def _get_default_vals(self, vals, default_vals=None):
        if default_vals is None:
            default_vals = []
        default_vals.append('display_pp')
        return super()._get_default_vals(
            vals, default_vals)
