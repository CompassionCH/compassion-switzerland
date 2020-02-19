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

    @api.multi
    def reconciliation_widget_preprocess(self):
        """
        Execute the same function in the parent class and then reorder the
        results by partner_id. This avoid having statements lines from the
        same partner at different place in the tree view.
        """

        result = super().reconciliation_widget_preprocess()

        # The ORDER BY is the change that order the lines in a more
        # comfortable way for reconciliation.
        sql_query = """SELECT stl.id
                        FROM account_bank_statement_line AS stl
                        WHERE stl.id IN %s
                        ORDER BY stl.partner_id
                """
        # List of statement_ids representing a statement line each.
        params = (tuple(result["st_lines_ids"]),)
        self.env.cr.execute(sql_query, params)
        results = [res["id"] for res in self.env.cr.dictfetchall()]
        result["st_lines_ids"] = results
        return result
