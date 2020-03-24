##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#    @author: Nicolas Badoux <n.badoux@hotmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import api, fields, models


class AccountStatement(models.Model):
    """ Adds a relation to a recurring invoicer. """

    _inherit = "account.bank.statement"

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    name = fields.Char(default=lambda b: b._default_name())

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    @api.model
    def _default_name(self):
        """ Find the appropriate sequence """
        journal_id = self.env.context.get("default_journal_id")
        if journal_id:
            journal = self.env["account.journal"].browse(journal_id)
            sequence = self.env["ir.sequence"].search([("name", "=", journal.name)])
            if sequence:
                return sequence.next_by_id()
        return ""
