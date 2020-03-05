##############################################################################
#
#    Copyright (C) 2017 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Marco Monzione <marco.mon@windowslive.com>, Emanuel Cino
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import api, models, fields


class ErrorsLog(models.Model):
    _name = 'error.log'
    _description = "Logging of errors"

    error_type = fields.Selection([
        ('B2S letters not sent', 'B2S letters not sent'),
        ('Letters in translation queue for too long',
         'Letters in translation queue for too long'),
        ('Sponsored child not in correct state',
         'Sponsored child not in correct state'),
        ('Invalid no money holds', 'Invalid no money holds'),
        ('Letters scanned in for too long',
         'Letters scanned in for too long'),
        ('Sponsored child has no sponsor',
         'Sponsored child has no sponsor')
    ])
    monitor_id = fields.Many2one('monitor.correct.errors')

    record = fields.Char()
    record_name = fields.Char()
    record_id = fields.Char()
    record_model = fields.Char()

    action = fields.Char()
    action_name = fields.Char()
    action_id = fields.Char()
    action_model = fields.Char()

    @api.model
    def get_error_type(self):
        return [v[0] for v in self.list_error_type()]

    @api.multi
    def format_record_url(self):
        self.ensure_one()
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')

        url = f'<a href="{base_url}/web#id={self.record_id}' \
              f'&view_type=form&model={self.record_model}">{self.record_name}</a>'
        return url

    @api.multi
    def format_action_url(self):
        self.ensure_one()
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')

        url = f'<a href="{base_url}/web#id={self.action_id}' \
              f'&view_type=form&model={self.action_model}">{self.action_name}</a>'

        return url
