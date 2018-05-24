# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Nicolas Badoux <n.badoux@hotmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import api, models, fields
from odoo.tools import file_open


class AmbassadorDetails(models.Model):
    _name = "ambassador.details"
    _description = "Ambassador Details"
    _rec_name = "partner_id"

    partner_id = fields.Many2one(
        'res.partner', required=True, ondelete='cascade')
    description = fields.Text(translate=True)
    quote = fields.Text(translate=True)
    picture_large = fields.Binary(
        string='Large picture', attachment=True,
        help='Optional large picture for your profile page'
    )
    picture_filename = fields.Char(compute='_compute_filename')
    thank_you_quote = fields.Html(
        compute='_compute_thank_you_quote',
        help='Used in thank you letters for donations linked to an event '
             'and to this partner.',
    )
    mail_copy_when_donation = fields.Boolean()

    @api.multi
    def _compute_filename(self):
        for details in self:
            partner_name = details.display_name
            details.picture_filename = partner_name + '-large.jpg'

    @api.multi
    def _compute_thank_you_quote(self):
        html_file = file_open(
            'partner_compassion/static/src/html/thank_you_quote_template.html')
        template_html = unicode(html_file.read())
        for details in self:
            html_vals = {
                u'img_alt': details.display_name,
                u'image_data': details.partner_id.with_context(
                    bin_size=False).image,
                u'text': details.quote
            }
            details.thank_you_quote = template_html.format(**html_vals)
