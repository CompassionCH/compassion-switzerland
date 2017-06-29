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
import logging

from time import sleep
from odoo import fields, models, api

logger = logging.getLogger(__name__)


class BulkGeoNameEncoder(models.TransientModel):
    _inherit = "geoengine.geoname.encoder"

    encode_missing = fields.Boolean('Encode missing addresses')

    def encode(self, cursor, uid, wiz_id, context=None):
        add_obj = self.pool['res.partner']
        current = self.browse(cursor, uid, wiz_id, context)
        if current.encode_missing:
            add_ids = add_obj.search(cursor, uid, [
                ('geo_point', '=', False),
            ], context=context)
            current.add_to_encode = add_obj.browse(
                cursor, uid, add_ids, context)
        return super(BulkGeoNameEncoder, self).encode(
            cursor, uid, wiz_id, context)

    @api.model
    def geocode_all_cron(self, limit=None, search_attr=None):
        logger.info("CRON for geocoding addresses started.")
        search = [
            ('date_localization', '=', False)
        ]
        if search_attr is not None:
            search.extend(search_attr)
        partners = self.env['res.partner'].search(search, limit=limit)
        total = len(partners)
        count = 1
        logger.info(
            "Found {} partners to update with mapquestapi.".format(total))
        for partner in partners:
            if count % 10 == 0:
                logger.info("... mapquestapi [{}/{}]".format(count, total))
            partner.geocode_address()
            # Limit the calls to API
            sleep(1)
            count += 1
        partners = partners.filtered('geo_point')
        total = len(partners)
        logger.info(
            "{} partners have no valid coordinates. Calling geoname service."
            .format(total)
        )
        partners.geocode_from_geonames()
        logger.info("CRON for geocoding addresses finished!")
        return True
