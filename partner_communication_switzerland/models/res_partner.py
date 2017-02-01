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

from openerp import api, models, fields, _


class ResPartnerTitle(models.Model):
    """
    Adds salutation and gender fields.
    """
    _inherit = 'res.partner.title'
    gender = fields.Selection([
        ('M', 'Male'),
        ('F', 'Female'),
    ])
    plural = fields.Boolean()


class ResPartner(models.Model):
    """
    Add method to send all planned communication of sponsorships.
    """
    _name = 'res.partner'
    _inherit = ['res.partner', 'translatable.model']

    salutation = fields.Char(compute='_get_salutation')
    gender = fields.Selection(related='title.gender')

    @api.multi
    def _get_salutation(self):
        for partner in self:
            if partner.is_company:
                partner.salutation = _("Dear friends of compassion")
            else:
                title = partner.title
                title_salutation = self.env['ir.advanced.translation'].get(
                    'salutation', female=title.gender == 'F',
                    plural=title.plural
                ).title()
                title_name = title.name
                if self.env.lang != 'de_DE':
                    title_name = title_name.lower()
                partner.salutation = title_salutation + ' ' + \
                    title_name + ' ' + partner.lastname
