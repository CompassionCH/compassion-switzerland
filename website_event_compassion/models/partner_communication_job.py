# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models, api


class CommunicationJob(models.Model):
    _inherit = "partner.communication.job"

    @api.multi
    def get_trip_down_payment_attachment(self):
        """
        TODO Return the BVR attachment for down payment
        :return: dict {attachment_name: [report_name, pdf_data]}
        """
        self.ensure_one()
        return {}

    @api.multi
    def get_trip_payment_attachment(self):
        """
        TODO Return the BVR attachment for trip payment
        :return: dict {attachment_name: [report_name, pdf_data]}
        """
        self.ensure_one()
        return {}
