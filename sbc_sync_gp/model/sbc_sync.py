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

from openerp import fields, models, api
from openerp.addons.mysql_connector.model.mysql_connector \
    import mysql_connector


class sbcSync(models.Model):
    _inherit = 'res.config.installer'
    _name = 'sbc.sync'

    partners_import_informations = fields.Text(
        'Partners importation informations')
    countries_import_informations = fields.Text(
        'Countries importation informations')
    partners_import_errors_visibility = fields.Boolean(
        'visibilityPartners', default=False)
    countries_import_errors_visibility = fields.Boolean(
        'visibilityCountries', default=False)

    @api.multi
    def import_countries_spoken_languages(self):
        # Select all spoken_langs with Country ISO3166
        self.partners_import_errors_visibility = False
        self.countries_import_errors_visibility = True
        self.countries_import_informations = False
        mySql_connector = mysql_connector()
        countries_spoken_langs_query = "SELECT `IDLANGUES`, `ISO3166` FROM\
        `langueparlee` INNER JOIN `pays` ON\
        `langueparlee`.`CODEGA` = `pays`.`ISO3166`"
        countries_spoken_langs = mySql_connector.selectAll(
            countries_spoken_langs_query)
        # to display informations
        # [0] = Number of tuple country - language successfully imported
        #   in odoo
        # [1] = Number of tuple country - language allready imported in odoo
        # [2] = Number of iso languages reccords not found in odoo
        # [3] = Number of country not found in odoo (tuple partner - language)
        import_informations_local = [[] for x in range(4)]
        # upsert Countries spoken_langs
        for spoken_lang in countries_spoken_langs:
            country = self.env['compassion.country'].search([(
                'iso_code', '=', spoken_lang['ISO3166'])], limit=1)
            if country:
                lang_to_insert = self.env['res.lang.compassion'].search([(
                    'ISO_code', '=', spoken_lang['IDLANGUES'])], limit=1)
                if lang_to_insert:
                    if lang_to_insert not in country.spoken_langs:
                        country.spoken_langs += lang_to_insert
                        import_informations_local[0].append(lang_to_insert)
                    else:
                        import_informations_local[1].append(lang_to_insert)
                else:
                    import_informations_local[2].append(
                        spoken_lang['IDLANGUES'])
            else:
                import_informations_local[3].append(str(
                    spoken_lang['ISO3166']) + " - " + str(
                    spoken_lang['IDLANGUES']) + '\n')
        # Display importation informations on countries_import_informations
        self.countries_import_informations = "Number of tuple country \
- language in GP : " + str(len(countries_spoken_langs)) + '\n'
        self.countries_import_informations += "Number of tuple country \
- language successfully imported in odoo : " + str(
            len(import_informations_local[0])) + '\n'
        self.countries_import_informations += "Number of tuple country \
- language allready imported in odoo : " + str(
            len(import_informations_local[1])) + '\n'
        self.countries_import_informations += "Number of iso languages \
reccords not found in odoo : " + str(
            len(import_informations_local[2])) + '\n' + '\n'
        unique_lang = []
        for lang in import_informations_local[2]:
            if lang not in unique_lang and str(lang) != "":
                unique_lang.append(lang)
        self.countries_import_informations += "Unique iso language not \
found in odoo : " + str(len(unique_lang)) + '\n'
        for lang in unique_lang:
            self.countries_import_informations += str(lang) + '\n'
        self.countries_import_informations += '\n' + "Number of country not \
found in odoo (tuple country - language) : " + str(
            len(import_informations_local[3])) + '\n'
        for partner in import_informations_local[3]:
            self.countries_import_informations += str(partner)
        # Return sbc.sync1 view
        return {
            'type': 'ir.actions.act_window',
            'name': 'SBC sync - Import spoken languages',
            'res_model': 'sbc.sync',
            'res_id': 1,
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'current',
        }

    @api.multi
    def import_partners_spoken_languages(self):
        # Select all spoken_langs with Partner CODEGA
        self.partners_import_errors_visibility = True
        self.countries_import_errors_visibility = False
        self.partners_import_informations = False
        mySql_connector = mysql_connector()
        partners_spoken_langs_query = "SELECT `IDLANGUES`, `id_erp` FROM\
        `langueparlee` INNER JOIN `adresses` ON\
        `langueparlee`.`CODEGA` = `adresses`.`CODEGA` WHERE\
        `adresses`.`id_erp` IS NOT NULL"
        partners_spoken_langs = mySql_connector.selectAll(
            partners_spoken_langs_query)
        # to display informations
        # [0] = Number of tuple partner - language successfully imported in
        #   odoo
        # [1] = Number of tuple partner - language allready imported in odoo
        # [2] = Number of iso languages reccords not found in odoo
        # [3] = Number of partner not found in odoo (tuple partner - language)
        import_informations_local = [[] for x in range(4)]
        # upsert Partners spoken_langs
        for spoken_lang in partners_spoken_langs:
            partner = self.env['res.partner'].search([(
                'id', '=', spoken_lang['id_erp'])], limit=1)
            if partner:
                lang_to_insert = self.env['res.lang.compassion'].search([(
                    'ISO_code', '=', spoken_lang['IDLANGUES'])], limit=1)
                if lang_to_insert:
                    if lang_to_insert not in partner.spoken_langs:
                        partner.spoken_langs += lang_to_insert
                        import_informations_local[0].append(lang_to_insert)
                    else:
                        import_informations_local[1].append(lang_to_insert)
                else:
                    import_informations_local[2].append(
                        spoken_lang['IDLANGUES'])
            else:
                import_informations_local[3].append(str(
                    spoken_lang['id_erp']) + " - " + str(
                    spoken_lang['IDLANGUES']) + '\n')
        # Display importation informations on countries_import_informations
        self.partners_import_informations = "Number of tuple partner \
- language in GP : " + str(len(partners_spoken_langs)) + '\n'
        self.partners_import_informations += "Number of tuple partner \
- language successfully imported in odoo : " + str(
            len(import_informations_local[0])) + '\n'
        self.partners_import_informations += "Number of tuple partner \
- language allready imported in odoo : " + str(
            len(import_informations_local[1])) + '\n'
        self.partners_import_informations += "Number of iso languages \
reccords not found in odoo : " + str(
            len(import_informations_local[2])) + '\n' + '\n'
        unique_lang = []
        for lang in import_informations_local[2]:
            if lang not in unique_lang and str(lang) != "":
                unique_lang.append(lang)
        self.partners_import_informations += "Unique iso language not found \
in odoo : " + str(len(unique_lang)) + '\n'
        for lang in unique_lang:
            self.partners_import_informations += str(lang) + '\n'
        self.partners_import_informations += '\n' + "Number of partner not \
found in odoo (tuple partner - language): " + str(
            len(import_informations_local[3])) + '\n'
        for partner in import_informations_local[3]:
            self.partners_import_informations += str(partner)
        # Return sbc.sync1 view
        return {
            'type': 'ir.actions.act_window',
            'name': 'SBC sync - Import spoken languages',
            'res_model': 'sbc.sync',
            'res_id': 1,
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'current',
        }

    @api.multi
    def action_close_popup(self):
        # Return sbc.sync1 view
        return {
            'type': 'ir.actions.act_window',
            'name': 'SBC sync - Import spoken languages',
            'res_model': 'sbc.sync',
            'res_id': 1,
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'current',
        }
