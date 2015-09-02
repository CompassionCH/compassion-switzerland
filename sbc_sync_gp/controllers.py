# -*- coding: utf-8 -*-
from openerp import http

# class ImportSpokenLangsForPartnerAndCountrySyncGp(http.Controller):
#     @http.route('/import_spoken_langs_for_partner_and_country_sync_gp/import_spoken_langs_for_partner_and_country_sync_gp/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/import_spoken_langs_for_partner_and_country_sync_gp/import_spoken_langs_for_partner_and_country_sync_gp/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('import_spoken_langs_for_partner_and_country_sync_gp.listing', {
#             'root': '/import_spoken_langs_for_partner_and_country_sync_gp/import_spoken_langs_for_partner_and_country_sync_gp',
#             'objects': http.request.env['import_spoken_langs_for_partner_and_country_sync_gp.import_spoken_langs_for_partner_and_country_sync_gp'].search([]),
#         })

#     @http.route('/import_spoken_langs_for_partner_and_country_sync_gp/import_spoken_langs_for_partner_and_country_sync_gp/objects/<model("import_spoken_langs_for_partner_and_country_sync_gp.import_spoken_langs_for_partner_and_country_sync_gp"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('import_spoken_langs_for_partner_and_country_sync_gp.object', {
#             'object': obj
#         })