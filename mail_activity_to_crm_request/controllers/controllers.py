# -*- coding: utf-8 -*-
# from odoo import http


# class MailActivityToCrmRequest(http.Controller):
#     @http.route('/mail_activity_to_crm_request/mail_activity_to_crm_request/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/mail_activity_to_crm_request/mail_activity_to_crm_request/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('mail_activity_to_crm_request.listing', {
#             'root': '/mail_activity_to_crm_request/mail_activity_to_crm_request',
#             'objects': http.request.env['mail_activity_to_crm_request.mail_activity_to_crm_request'].search([]),
#         })

#     @http.route('/mail_activity_to_crm_request/mail_activity_to_crm_request/objects/<model("mail_activity_to_crm_request.mail_activity_to_crm_request"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('mail_activity_to_crm_request.object', {
#             'object': obj
#         })
