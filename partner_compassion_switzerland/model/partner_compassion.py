# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################
from openerp import api, fields, models, _


class ResPartner(models.Model):
    """ This class upgrade the partners to match Compassion needs.
        It also synchronize all changes with the MySQL server of GP.
    """

    _inherit = 'res.partner'

    def _get_receipt_types(self):
        """ Display values for the receipt selection fields. """
        return [
            ('no', _('No receipt')),
            ('default', _('Default')),
            ('email', _('By e-mail')),
            ('paper', _('On paper'))]

    ##########################################################################
    #                        NEW PARTNER FIELDS                              #
    ##########################################################################
    ref = fields.Char(default=False)
    lang = fields.Selection(default=False)
    opt_out = fields.Boolean(default=True)
    nbmag = fields.Integer('Number of Magazines', size=2,
                           required=True, default=0)
    tax_certificate = fields.Selection(
        _get_receipt_types, required=True, default='default')
    thankyou_letter = fields.Selection(
        _get_receipt_types, _('Thank you letter'),
        required=True, default='default')
    calendar = fields.Boolean(
        help=_("Indicates if the partner wants to receive the Compassion "
               "calendar."), default=True)
    christmas_card = fields.Boolean(
        help=_("Indicates if the partner wants to receive the "
               "christmas card."), default=True)
    birthday_reminder = fields.Boolean(
        help=_("Indicates if the partner wants to receive a birthday "
               "reminder of his child."), default=True)
    abroad = fields.Boolean(
        'Abroad/Only e-mail',
        help=_("Indicates if the partner is abroad and should only be "
               "updated by e-mail"))

    @api.multi
    def get_unreconciled_amount(self):
        """Returns the amount of unreconciled credits in Account 1050"""
        self.ensure_one()
        mv_line_obj = self.env['account.move.line']
        move_line_ids = mv_line_obj.search([
            ('partner_id', '=', self.id),
            ('account_id.code', '=', '1050'),
            ('credit', '>', '0'),
            ('reconcile_id', '=', False)])
        res = 0
        for move_line in move_line_ids:
            res += move_line.credit
        return res

    ##########################################################################
    #                             VIEW CALLBACKS                             #
    ##########################################################################
    @api.multi
    def onchange_type(self, is_company):
        """ Put title 'Friends of Compassion for companies. """
        res = super(ResPartner, self).onchange_type(is_company)
        if is_company:
            res['value']['title'] = self.env.ref(
                'partner_compassion.res_partner_title_friends').id
        return res
