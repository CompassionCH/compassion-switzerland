# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp import api, models


class CompassionChild(models.TransientModel):
    """ Add keywords on all defined sendgrid templates.
    """
    _name = 'init.sendgrid.template'

    @api.model
    def init_templates(self):
        """ Add sendgrid template configuration and add substitutions. """
        major_revision_templates = self.env['email.template'].search([
            ('name', 'like', 'Major Revision'),
            ('sendgrid_template_ids', '=', False)
        ])
        sendgrid_template_obj = self.env['sendgrid.template']
        lang_template_obj = self.env['sendgrid.email.lang.template']
        de_template = sendgrid_template_obj.search([
            ('name', '=', 'General DE')])
        it_template = sendgrid_template_obj.search([
            ('name', '=', 'General IT')])
        fr_template = sendgrid_template_obj.search([
            ('name', '=', 'General FR')])
        for email_template in major_revision_templates:
            lang_template_obj.create({
                'email_template_id': email_template.id,
                'lang': 'de_DE',
                'sendgrid_template_id': de_template.id,
            })
            lang_template_obj.create({
                'email_template_id': email_template.id,
                'lang': 'fr_CH',
                'sendgrid_template_id': fr_template.id,
            })
            lang_template_obj.create({
                'email_template_id': email_template.id,
                'lang': 'it_IT',
                'sendgrid_template_id': it_template.id,
            })
            email_template.update_substitutions()
