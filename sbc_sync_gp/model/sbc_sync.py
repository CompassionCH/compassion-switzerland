# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014-2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emmanuel Mathier <emmanuel.mathier@gmail.com>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp import fields, models, api, _
from openerp.addons.mysql_connector.model.mysql_connector \
    import mysql_connector
import pdb

class sbcSync(models.Model):
    _inherit = 'res.config.installer'
    _name = 'sbc.sync'

    progress_bar = fields.Integer('Status')
    partners_import_errors = fields.Text('Partner not found in odoo')
    countries_import_errors = fields.Text('Countries not found in odoo')
    next_visibility = fields.Boolean('visibilityNext', default=True)
    partners_import_errors_visibility = fields.Boolean('visibilityPartners', default=False)
    countries_import_errors_visibility = fields.Boolean('visibilityCountries', default=False)


    @api.multi
    def import_countries_spoken_languages(self):
        # Select all spoken_langs with Country ISO3166
        self.next_visibility = False
        self.countries_import_errors = False
        mySql_connector = mysql_connector()
        countries_spoken_langs_query = "SELECT `IDLANGUES`, `ISO3166` FROM  `langueparlee` INNER JOIN `pays` ON `langueparlee`.`CODEGA` = `pays`.`ISO3166`"
        countries_spoken_langs = mySql_connector.selectAll(countries_spoken_langs_query)
        # upsert Partners spoken_langs
        for spoken_lang in countries_spoken_langs:
            country = self.env['compassion.country'].search([('iso_code', '=', spoken_lang['ISO3166'])], limit=1)
            if country:
                lang_to_insert = self.env['res.lang.compassion'].search([('ISO_code', '=', spoken_lang['IDLANGUES'])], limit=1)
                if lang_to_insert:     
                    if lang_to_insert not in country.spoken_langs:
                        country.spoken_langs += lang_to_insert
            else:
                self.countries_import_errors_visibility = True
                if self.countries_import_errors:
                    self.countries_import_errors += ", " + str(spoken_lang['ISO3166'])
                else:
                    self.countries_import_errors = str(spoken_lang['ISO3166'])
        return {
            'type': 'ir.actions.act_window',
            'name': 'SBC sync - Import spoken languages',
            'res_model': 'sbc.sync',
            'res_id': 1,
            'view_type': 'form',
            'view_mode': 'form',
            'target' : 'current',
        }


    @api.multi
    def import_partners_spoken_languages(self):
        # Select all spoken_langs with Partner CODEGA
        self.next_visibility = False
        self.partners_import_errors = False
        mySql_connector = mysql_connector()
        partners_spoken_langs_query = "SELECT `IDLANGUES`, `id_erp` FROM  `langueparlee` INNER JOIN `adresses` ON `langueparlee`.`CODEGA` = `adresses`.`CODEGA` WHERE `adresses`.`id_erp` IS NOT NULL"
        partners_spoken_langs = mySql_connector.selectAll(partners_spoken_langs_query)
        # upsert Partners spoken_langs
        for spoken_lang in partners_spoken_langs:
            partner = self.env['res.partner'].search([('id', '=', spoken_lang['id_erp'])], limit=1)
            if partner:
                lang_to_insert = self.env['res.lang.compassion'].search([('ISO_code', '=', spoken_lang['IDLANGUES'])], limit=1)
                if lang_to_insert:     
                    if lang_to_insert not in partner.spoken_langs:
                        partner.spoken_langs += lang_to_insert
            else:
                self.partners_import_errors_visibility = True
                if self.partners_import_errors:
                    self.partners_import_errors += ", " + str(spoken_lang['id_erp'])
                else:
                    self.partners_import_errors = str(spoken_lang['id_erp'])
        return {
            'type': 'ir.actions.act_window',
            'name': 'SBC sync - Import spoken languages',
            'res_model': 'sbc.sync',
            'res_id': 1,
            'view_type': 'form',
            'view_mode': 'form',
            'target' : 'current',
        }


    @api.multi
    def action_close_popup(self):
        self.next_visibility = False
        self.partners_import_errors = False
        self.countries_import_errors = False
        return {
            'type': 'ir.actions.act_window',
            'name': 'SBC sync - Import spoken languages',
            'res_model': 'sbc.sync',
            'res_id': 1,
            'view_type': 'form',
            'view_mode': 'form',
            'target' : 'current',
        }