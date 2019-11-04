# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging
from odoo import models

_logger = logging.getLogger(__name__)


class Geocoder(models.AbstractModel):
    _inherit = 'base.geocoder'

    def _raise_internet_access_error(self, error):
        # Don't raise error
        _logger.error(
            "Cannot contact geolocation servers. Please make sure that your "
            "Internet connection is up and running (%s).", error)
