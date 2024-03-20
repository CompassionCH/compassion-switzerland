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

    create_support_request = fields.Boolean(
        help="A support request will be created for the activity",
    )

    request_category_id = fields.Many2one(comodel_name ='crm.claim.category', string='Category')
    request_stage_id = fields.Many2one(comodel_name ='crm.claim.stage', string='Stage')

    @api.model
    def create(self, values):
        activity = super(MailActivity, self).create(values)

        # Create the schedule activity to support request if the corresponding user option is selected
        if activity.create_support_request:
            # Compute the code
            code = self.env["ir.sequence"].next_by_code("crm.claim.activity")

            # Create the request
            record = self.env['crm.claim'].create({
                                        'user_id': activity.user_id.id,
                                        'code': code,
                                        'subject': activity.summary,
                                        'name': activity.summary,
                                        'categ_id': activity.request_category_id.id,
                                        'stage_id': activity.request_stage_id.id
                                          })

            # Message in the chatter of the record where the request has been created with link to the module
            # where the activity has been created
            related_record_url = f"{activity.get_base_url()}/web#id={activity.res_id}&view_type=form&model={activity.res_model}"
            record.message_post(body=f"A schedule activity was created. <a href='{related_record_url}'>View related record</a>")

        return activity