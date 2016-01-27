# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Roman Zoller
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp import models, api, fields
from cgi import escape


class TemplateList(models.Model):
    _name = 'sponsorship.templatelist'

    name_id = fields.Many2one('sponsorship.templatename', 'Name')
    lang = fields.Char()
    layout_template_id = fields.Many2one('sendgrid.template')
    text_template_id = fields.Many2one('email.template')
    intro = fields.Char()
    tweet = fields.Char()

    @api.model
    def create(self, vals):
        if 'tweet' in vals:
            vals['tweet'] = escape(vals['tweet'])
        return super(TemplateList, self).create(vals)

    @api.multi
    def write(self, vals):
        if 'tweet' in vals:
            vals['tweet'] = escape(vals['tweet'])
        return super(TemplateList, self).write(vals)
