# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from collections import defaultdict
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
import logging
import pytz
import random

from odoo import api, exceptions, fields, models, _
from odoo.osv import expression

from odoo.tools.misc import clean_context
from odoo.addons.base.models.ir_model import MODULE_UNINSTALL_FLAG

_logger = logging.getLogger(__name__)

class MailActivity(models.Model):
    _inherit = 'mail.activity'

    convert_activity_to_sup_req = fields.Boolean(
        "Convert activity to support request",
        help="A support request will be created for the activity",
        default=False,
    )

    category = fields.Many2one(comodel_name ='crm.claim.category', string='Category')
    stage = fields.Many2one(comodel_name ='crm.claim.stage', string='Stage')

    @api.model
    def create(self, values):
        activity = super(MailActivity, self).create(values)
        need_sudo = False
        try:  # in multicompany, reading the partner might break
            partner_id = activity.user_id.partner_id.id
        except exceptions.AccessError:
            need_sudo = True
            partner_id = activity.user_id.sudo().partner_id.id

        # send a notification to assigned user; in case of manually done activity also check
        # target has rights on document otherwise we prevent its creation. Automated activities
        # are checked since they are integrated into business flows that should not crash.
        if activity.user_id != self.env.user:
            if not activity.automated:
                activity._check_access_assignation()
            if not self.env.context.get('mail_activity_quick_update', False):
                if need_sudo:
                    activity.sudo().action_notify()
                else:
                    activity.action_notify()

        self.env[activity.res_model].browse(activity.res_id).message_subscribe(partner_ids=[partner_id])
        if activity.date_deadline <= fields.Date.today():
            self.env['bus.bus'].sendone(
                (self._cr.dbname, 'res.partner', activity.user_id.partner_id.id),
                {'type': 'activity_updated', 'activity_created': True})

        # Create the schedule activity to support request if the corresponding user option is selected
        if activity.convert_activity_to_sup_req:

            # Code definition for the new request 'ACT-XXX'
            # Retrieve last request created with an activity
            last_instance = self.env['crm.claim'].search([('code', 'like', 'A%')], order="create_date desc", limit=1)
            if len(last_instance) == 0:
                # If no request found the digits of the code is defined to 1
                new_code = 'ACT-1'
            else:
                # Otherwise we increase the digit of 1 unit
                previous_code = last_instance.code
                new_code = previous_code[0:4] + str(int(previous_code[4:]) + 1)

            # Create the request
            record = self.env['crm.claim'].create({
                                        'user_id': activity.user_id.id,
                                        'code': new_code,
                                        'subject': activity.summary,
                                        'name': 'some random stuff to debug',
                                        'categ_id': activity.category.id,
                                        'stage_id': activity.stage.id
                                          })

            record_url = self.env['ir.config_parameter'].sudo().get_param(
                'web.base.url') + "/web#id=%s&view_type=form&model=%s" % (record.id, 'crm.claim')

            # # Message in the chatter of the record where the activity has been created with link to the request
            # related_record = self.env[activity.res_model].browse(activity.res_id)
            # if related_record:
            #     related_record.message_post(body=f'New request "{activity.summary}" has been created: <a href="{record_url}">View request</a>')

            # Message in the chatter of the record where the request has been created with link to the module
            # where the activity has been created
            related_model = activity.res_model
            related_record_id = activity.res_id
            if related_model and related_record_id:
                related_record_url = self.env['ir.config_parameter'].sudo().get_param(
                    'web.base.url') + f"/web#id={related_record_id}&view_type=form&model={related_model}"
            else:
                related_record_url = ""
            # Post the message in the chatter of the claim request
            record.message_post(body=f"A schedule activity was created. <a href='{related_record_url}'>View related record</a>")

        return activity