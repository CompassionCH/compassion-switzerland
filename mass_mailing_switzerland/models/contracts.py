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
import simplejson

from odoo.addons.child_compassion.models.compassion_hold import HoldType
from odoo.addons.queue_job.job import job, related_action

from odoo import api, models, fields


class Contracts(models.Model):
    _inherit = 'recurring.contract'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    mailing_campaign_id = fields.Many2one('mail.mass_mailing.campaign')
