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


from openerp import models, api


class MailFollowers(models.Model):
    """ Prevent having too much followers in mail threads.
    """
    _inherit = 'mail.followers'

    @api.model
    def _mail_restrict_follower_selection_get_domain(self, model):
        parameter_name = 'mail_restrict_follower_selection.domain'
        return self.env['ir.config_parameter'].get_param(
            '%s.%s' % (parameter_name, model),
            self.env['ir.config_parameter'].get_param(
                parameter_name, default='[]')
        )

    @api.model
    def create(self, vals):
        """
        Remove partners not in domain selection of module
        mail_restrict_follower_selection
        """
        model = vals['res_model']
        res_id = vals['partner_id']
        domain = self._mail_restrict_follower_selection_get_domain(model)
        allowed = self.env['res.partner'].search(eval(domain))
        if allowed and res_id in allowed.ids:
            return super(MailFollowers, self).create(vals)
        return self
