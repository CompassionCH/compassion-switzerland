# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Roman Zoller
#
#    The licence is in the file __openerp__.py
#
##############################################################################

import logging

from openerp.addons.mysql_connector.model.mysql_connector \
    import mysql_connector
from openerp import api, models

_logger = logging.getLogger(__name__)


class ImportSpokenLang(models.TransientModel):
    _name = 'import_spoken_lang'

    @api.model
    def run_import(self):
        """ Import spoken language data from GP.
        Data is imported in two groups:
        - For every partner, the set of languages that the person speaks
        - For every country, the set of languages that are spoken there """

        # Initialize
        mysql = mysql_connector()
        self._create_language_dict()

        # Import spoken languages for partners
        _logger.info("Import spoken languages for partners...")
        sql = "SELECT a.id_erp as partner_id, lp.IDLANGUES as language_iso " \
              "FROM langueparlee lp JOIN adresses a ON lp.CODEGA = a.CODEGA " \
              "WHERE a.id_erp IS NOT NULL"
        i = 0
        result = mysql.selectAll(sql)
        for i, row in enumerate(result, start=1):
            self._add_partner_language(row['partner_id'], row['language_iso'])
            if i % 100 == 0:
                _logger.info("Import spoken languages for partners: {}/{}"
                             .format(i, len(result)))
        _logger.info("Import spoken languages for partners: done!")

        # Import spoken languages for countries
        _logger.info("Import spoken languages for countries...")
        sql = "SELECT lp.CODEGA as country_iso, lp.IDLANGUES as language_iso " \
              "FROM langueparlee lp JOIN pays p ON lp.CODEGA = p.ISO3166"
        for row in mysql.selectAll(sql):
            self._add_country_language(row['country_iso'], row['language_iso'])
        _logger.info("Import spoken languages for countries: done!")

        _logger.info("Language import successful!")

    def _create_language_dict(self):
        """ Retrieve language table and keep mapping
        from ISO code to id in memory. """
        languages = self.env['res.lang.compassion'].search([])
        self._language_iso_to_id = {}
        for language in languages:
            self._language_iso_to_id[language.code_iso] = language.id

    def _add_partner_language(self, partner_id, language_iso):
        partner = self.env['res.partner'].search([['id', '=', partner_id]])
        if partner:
            if language_iso in self._language_iso_to_id:
                language_id = self._language_iso_to_id[language_iso]
                partner.write({'spoken_langs_ids': [(4, language_id)]})
            else:
                _logger.warning("language not found: {}".format(language_iso))
        else:
            _logger.warning("partner id not found: {}".format(partner_id))

    def _add_country_language(self, country_iso, language_iso):
        countries = self.env['compassion.country']
        country = countries.search([['iso_code', '=', country_iso]])
        if country:
            if language_iso in self._language_iso_to_id:
                language_id = self._language_iso_to_id[language_iso]
                country.write({'spoken_langs_ids': [(4, language_id)]})
            else:
                _logger.warning("language not found: {}".format(language_iso))
        else:
            _logger.warning("country not found: {}".format(country_iso))
