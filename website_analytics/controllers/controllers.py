# -*- coding: utf-8 -*-
# from odoo import http


# class WebsiteAnalytics(http.Controller):
#     @http.route('/website_analytics/website_analytics/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/website_analytics/website_analytics/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('website_analytics.listing', {
#             'root': '/website_analytics/website_analytics',
#             'objects': http.request.env['website_analytics.website_analytics'].search([]),
#         })

#     @http.route('/website_analytics/website_analytics/objects/<model("website_analytics.website_analytics"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('website_analytics.object', {
#             'object': obj
#         })
