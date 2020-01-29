##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import api, models


class CompassionChild(models.TransientModel):
    """ Add keywords on all defined sendgrid templates.
    """
    _name = 'init.sendgrid.template'

    @api.model
    def init_templates(self):
        """ Add sendgrid template configuration and add substitutions. """
        templates = self.env['mail.template'].search([
            '|', '|', '|',
            ('name', 'like', 'Major Revision'),
            ('name', 'like', 'Child Lifecycle'),
            ('name', 'like', 'Sponsorship'),
            ('name', 'in', [
                'Beneficiary Hold Removal', 'First letter system changed',
                'New letter', 'Default Communication'
            ]),
            ('sendgrid_template_ids', '=', False)
        ])
        sendgrid_template_obj = self.env['sendgrid.template']
        lang_template_obj = self.env['sendgrid.email.lang.template']
        test_template = sendgrid_template_obj.search([
            ('name', '=', 'Test Template')])
        de_template = sendgrid_template_obj.search([
            ('name', '=', 'General DE')]) or test_template
        it_template = sendgrid_template_obj.search([
            ('name', '=', 'General IT')]) or test_template
        fr_template = sendgrid_template_obj.search([
            ('name', '=', 'General FR')]) or test_template
        if not test_template or fr_template:
            return
        for email_template in templates:
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
