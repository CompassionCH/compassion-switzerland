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
    short_salutation = fields.Char(compute='_get_salutation')
    gender = fields.Selection(related='title.gender')
    letter_delivery_preference = fields.Selection(
        selection='_get_delivery_preference',
        default='auto_digital',
        required=True,
        help='Delivery preference for Child Letters',
    )

    @api.multi
    def _get_salutation(self):
        for p in self:
            partner = p.with_context(lang=p.lang)
            if partner.title and partner.firstname and not partner.is_company:
                title = partner.title
                title_salutation = partner.env['ir.advanced.translation'].get(
                    'salutation', female=title.gender == 'F',
                    plural=title.plural
                ).title()
                title_name = title.name
                p.salutation = title_salutation + ' ' + \
                    title_name + ' ' + partner.lastname
                p.short_salutation = title_salutation + ' ' + partner.firstname
            else:
                p.salutation = _("Dear friends of compassion")
                p.short_salutation = _("Dear friends of compassion")
