# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2017 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp import models, api, fields, _
from openerp.exceptions import Warning


class ChangeTextWizard(models.TransientModel):
    _inherit = 'partner.communication.change.text.wizard'

    state = fields.Char(default=lambda s: s._default_state())
    event_name = fields.Char()
    event_text = fields.Html()
    ambassador_id = fields.Many2one(
        'res.partner', 'Ambassador', compute='_compute_ambassador',
        inverse='_inverse_ambassador'
    )
    ambassador_name = fields.Char()
    ambassador_text = fields.Html()

    @api.multi
    def _compute_ambassador(self):
        communications = self._get_communications()
        ambassador = communications.mapped('ambassador_id')
        if len(ambassador) == 1:
            for wizard in self:
                wizard.ambassador_id = ambassador

    @api.multi
    def _inverse_ambassador(self):
        ambassador = self.ambassador_id
        if ambassador:
            if not ambassador.ambassador_quote:
                ambassador.ambassador_quote = self.ambassador_text
            communications = self._get_communications()
            inv_lines = communications.get_objects()
            inv_lines.write({'user_id': self.ambassador_id.id})
            communications.write({'ambassador_id': self.ambassador_id.id})

    @api.model
    def _get_communications(self):
        context = self.env.context
        communications = self.env[context['active_model']].browse(
            context['active_ids'])
        lang = communications.mapped('partner_id.lang')[0]
        return communications.with_context(lang=lang)

    @api.model
    def _default_state(self):
        communications = self._get_communications()
        event = communications.mapped('event_id')
        if event:
            if len(event) > 1:
                raise Warning(_("You can only change one event at a time."))
            return 'event'
        else:
            return 'edit'

    @api.onchange('state')
    def onchange_state(self):
        if self.state == 'event' and not self.event_name:
            communications = self._get_communications()
            event = communications.mapped('event_id')
            self.event_name = event.name
            self.event_text = event.thank_you_text
            self._compute_ambassador()

    @api.onchange('ambassador_id')
    def onchange_ambassador(self):
        ambassador = self.ambassador_id
        if ambassador:
            self.ambassador_name = ambassador.full_name
            self.ambassador_text = ambassador.ambassador_quote

    @api.multi
    def update(self):
        """ Refresh the texts of communications given the new template. """
        self.ensure_one()
        communications = self._get_communications()
        event = communications.mapped('event_id')
        if event:
            config = communications.mapped('config_id')
            if len(config) != 1:
                raise Warning(
                    _("You can only update text on one communication type at "
                      "time."))
            if self.event_text != event.thank_you_text:
                event.thank_you_text = self.event_text
            ambassador = self.ambassador_id
            if ambassador and self.ambassador_text != \
                    ambassador.ambassador_quote:
                ambassador.ambassador_quote = self.ambassador_text
            template = config.email_template_id
            new_texts = template.render_template_batch(
                self.template_text, template.model, communications.ids)
            for comm in communications:
                comm.body_html = new_texts[comm.id].replace(
                    event.name, self.event_name)
                if ambassador:
                    comm.body_html = comm.body_html.replace(
                        ambassador.full_name, self.ambassador_name or '')
            return True
        else:
            return super(ChangeTextWizard, self).update()

    @api.multi
    def get_preview(self):
        if self.state == 'event':
            communication = self._get_communications()[0]
            event = communication.mapped('event_id')
            ambassador = self.ambassador_id
            template = communication.email_template_id
            preview = template.render_template_batch(
                self.template_text, template.model, communication.ids)[
                communication.id].replace(
                event.name, self.event_name or '')
            if event.thank_you_text:
                preview = preview.replace(
                    event.thank_you_text, self.event_text or '')
            if ambassador:
                preview = preview.replace(
                    ambassador.full_name, self.ambassador_name or '').replace(
                    ambassador.ambassador_quote, self.ambassador_text or '')
            self.write({
                'state': 'preview',
                'preview': preview
            })
            return self._reload()
        else:
            return super(ChangeTextWizard, self).get_preview()

    @api.multi
    def edit(self):
        event = self._get_communications().mapped('event_id')
        if event:
            self.state = 'event'
        else:
            self.state = 'edit'
        return self._reload()
