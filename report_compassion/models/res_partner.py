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
import re

from openerp import api, models, fields


class ResPartner(models.Model):
    """ Add fields for retrieving values for communications.

    - Short address
        Mr. John Doe
        Street
        City
        Country
    """
    _inherit = 'res.partner'

    short_address = fields.Char(compute='_compute_address')

    @api.multi
    def _compute_address(self):
        # Replace line returns
        p = re.compile('\\n+')
        for partner in self:
            if not partner.is_company:
                res = partner.title.shortcut + ' '
                res += partner.firstname + ' ' + partner.lastname + '<br/>'
            else:
                res = partner.name + '<br/>'
            res += partner.contact_address
            partner.short_address = p.sub('<br/>', res)
