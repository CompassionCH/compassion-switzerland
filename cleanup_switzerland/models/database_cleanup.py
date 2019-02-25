# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2017 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging

from datetime import date

from dateutil.relativedelta import relativedelta

from odoo import api, models
from psycopg2 import sql, ProgrammingError


_logger = logging.getLogger(__name__)


class DatabaseCleanup(models.AbstractModel):
    _name = 'database.cleanup.switzerland'

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    @api.model
    def cleanup(self):
        """
        We use this method called in a CRON in order to clean our database.
        :return:
        """
        self.clean_mail_message()
        # Clean emails that are not valid (created by incoming messages)
        mail_ids = self.env['mail.mail'].search([
            ('state', '=', 'outgoing'),
            '|', ('author_id', '=', False),
            ('author_id.user_ids', '=', False)
        ]).ids
        self.env.cr.execute(
            "DELETE FROM mail_mail WHERE id = ANY (%s)",
            [mail_ids]
        )
        return True

    def clean_mail_message(self):
        # Clean messages not related to an existing object
        _logger.info("Database cleanup for Compassion Switzerland started")
        self.env.cr.execute(
            "DELETE FROM mail_message WHERE model IS NULL"
        )
        models = self.env['ir.model'].search([]).mapped('model')
        for model in models:
            table = model.replace('.', '_')
            try:
                # sql libraries do avoid SQL injection, plus this code
                # does not take user input.
                # pylint: disable=sql-injection
                self.env.cr.execute(sql.SQL(
                    "DELETE FROM mail_message WHERE model=%s AND NOT EXISTS ("
                    "    SELECT 1 FROM {} WHERE id = res_id);"
                ).format(sql.Identifier(table)), [model])
                # Commit the cleanup
                count = self.env.cr.rowcount
                self.env.cr.commit()  # pylint: disable=invalid-commit
                _logger.info(
                    '{} mail_message for invalid {} objects removed'.format(
                        count, model)
                )
            except ProgrammingError:
                self.env.cr.rollback()

        # Delete old messages for old objects not useful
        today = date.today()
        limit = today - relativedelta(years=1)
        limit_str = limit.strftime("%Y-%m-%d")
        self.env.cr.execute(
            "DELETE FROM mail_message WHERE model = 'account.invoice' "
            "AND res_id IN (SELECT id FROM account_invoice WHERE state IN ("
            "'cancel', 'paid') AND date_invoice < %s LIMIT 1000)", [limit_str]
        )
        count = self.env.cr.rowcount
        self.env.cr.commit()  # pylint: disable=invalid-commit
        _logger.info('{} old invoice messages removed'.format(count))

        self.env.cr.execute(
            "DELETE FROM mail_message WHERE model='gmc.message.pool' AND "
            "res_id IN (SELECT id FROM gmc_message_pool WHERE state ="
            "'success' LIMIT 1000)"
        )
        count = self.env.cr.rowcount
        self.env.cr.commit()  # pylint: disable=invalid-commit
        _logger.info('{} old gmc_pool messages removed'.format(count))

        self.env.cr.execute(
            "DELETE FROM mail_message WHERE model='partner.communication.job' "
            "AND res_id IN (SELECT id FROM partner_communication_job WHERE "
            "state = 'cancel' OR (state = 'done' AND sent_date < %s)"
            "LIMIT 1000)",
            [limit_str]
        )
        count = self.env.cr.rowcount
        self.env.cr.commit()  # pylint: disable=invalid-commit
        _logger.info('{} old partner_communication messages removed'.format(
            count))

        self.env.cr.execute(
            "DELETE FROM mail_message WHERE model='correspondence' AND "
            "res_id IN (SELECT id FROM correspondence WHERE "
            "state IN ('cancel') OR (state = 'done' AND sent_date < %s))",
            [limit_str]
        )
        count = self.env.cr.rowcount
        self.env.cr.commit()  # pylint: disable=invalid-commit
        _logger.info('{} old partner_communication messages removed'.format(
            count))

        self.env.cr.execute(
            "DELETE FROM mail_message WHERE model='recurring.contract' AND "
            "res_id IN (SELECT id FROM recurring_contract WHERE "
            "state IN ('terminated', 'cancelled') AND end_date < %s)",
            [limit_str]
        )
        count = self.env.cr.rowcount
        self.env.cr.commit()  # pylint: disable=invalid-commit
        _logger.info('{} old recurring_contract messages removed'.format(
            count))

        self.env.cr.execute(
            "DELETE FROM mail_message WHERE model='account.analytic.account' "
            "AND date < %s", [limit_str]
        )
        count = self.env.cr.rowcount
        self.env.cr.commit()  # pylint: disable=invalid-commit
        _logger.info('{} old analytic_account messages removed'.format(count))
