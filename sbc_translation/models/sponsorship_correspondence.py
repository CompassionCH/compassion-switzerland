# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Stephane Eicher <eicher31@hotmail.com>
#
#    The licence is in the file __openerp__.py
#
##############################################################################
import pdb

from openerp import models, api


class SponsorshipCorrespondence(models.Model):
    """ This class intecept a letter befor it can be sending and sending
    to local translate plateforme"""

    _inherit = 'sponsorship.correspondence'

    ##########################################################################
    #                              ORM METHODS                               #
    ##########################################################################
    @api.model
    def create(self, vals):
        """ Create a message for sending the CommKit. """
        pdb.set_trace()
        sponsorship = self.env['recurring.contract'].browse(
            vals['sponsorship_id'])
        if sponsorship.reading_language.id == vals['original_language_id']:
            letter = super(SponsorshipCorrespondence, self.with_context(
                no_comm_kit=False)).create(vals)
        else:
            letter = super(SponsorshipCorrespondence, self.with_context(
                no_comm_kit=True)).create(vals)
            self.alternative()
        return letter

    def alternative(self):
        pass
