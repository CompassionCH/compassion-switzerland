from odoo import api, models
from odoo.osv import expression
from odoo.addons.queue_job.job import job


class AccountReconciliationWidget(models.AbstractModel):
    _inherit = "account.reconciliation.widget"

    @api.model
    def get_bank_statement_line_data(self, st_line_ids, excluded_ids=None):
        """
        Reorder the results by partner_id. This avoid having statements lines from the
        same partner at different place in the tree view.
        """
        results = super().get_bank_statement_line_data(st_line_ids, excluded_ids)
        results["lines"] = sorted(
            results["lines"],
            key=lambda l: l["st_line"].get("partner_id", l["st_line"]["id"] * 500000)
        )
        return results

    @api.model
    def get_move_lines_for_bank_statement_line(self, st_line_id, partner_id=None,
                                               excluded_ids=None, search_str=False,
                                               offset=0, limit=None):
        """
        Propose up to 12 move lines for a complete year, and avoid too much propositions
        """
        if limit is not None and limit < 12:
            limit = 12
        if limit is None:
            limit = 40
        return super().get_move_lines_for_bank_statement_line(
            st_line_id, partner_id, excluded_ids, search_str, offset, limit
        )

    def _prepare_move_lines(self, move_lines, target_currency=False, target_date=False,
                            recs_count=0):
        """
        Sort move lines according to Compassion criterias :
        Move line for current month at first,
        Then other move_lines, from the oldest to the newest.
        :param move_lines:
        :param target_currency:
        :param target_date:
        :return:
        """

        def _sort_move_line(move_line):
            limit_year = target_date.year - 5
            index = limit_year
            mv_date = move_line.date_maturity or move_line.date
            if (
                    mv_date.month == target_date.month
                    and mv_date.year == target_date.year
            ):
                index += 1
            else:
                index += mv_date.month + (mv_date.year - limit_year) * 12
            return index

        move_lines = move_lines.sorted(_sort_move_line)
        return super()._prepare_move_lines(
            move_lines, target_currency, target_date, recs_count)

    def _domain_move_lines_for_reconciliation(self, st_line, aml_accounts, partner_id,
                                              excluded_ids=None, search_str=False):
        """
        Restrict propositions to move lines with same references as bank statement line
        """
        domain = super()._domain_move_lines_for_reconciliation(
            st_line, aml_accounts, partner_id, excluded_ids, search_str
        )
        if st_line.ref:
            domain = expression.AND([domain, [("ref", "ilike", st_line.ref)]])
        return domain

    @api.model
    def _process_move_lines(self, move_line_ids, new_mv_line_dicts):
        """ Run reconciliation in a job. """
        self.with_delay()._process_reconciliation(move_line_ids, new_mv_line_dicts)
        return True

    @api.model
    @job(default_channel="root.bank_reconciliation")
    def _process_reconciliation(self, move_line_ids, new_mv_line_dicts):
        """Bank statement line reconciliation job"""
        super()._process_move_lines(move_line_ids, new_mv_line_dicts)
        return True
