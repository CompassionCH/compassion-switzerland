##############################################################################
#
#    Copyright (C) 2017-2020 Compassion CH (http://www.compassion.ch)
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
    _name = "database.cleanup.switzerland"
    _description = "Clean switzerland database"

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    @api.model
    def cleanup(self):
        """
        We use this method called in a CRON in order to clean our database.
        :return:
        """
        self.with_delay().clean_mail_message()
        # Clean emails that are not valid (created by incoming messages)
        mail_ids = (
            self.env["mail.mail"]
                .search(
                [
                    ("state", "=", "outgoing"),
                    "|",
                    ("author_id", "=", False),
                    ("author_id.user_ids", "=", False),
                ]
            )
            .ids
        )
        self.env.cr.execute("DELETE FROM mail_mail WHERE id = ANY (%s)", [mail_ids])
        count = self.env.cr.rowcount
        _logger.info("{} invalid mail.mail removed".format(count))
        self.with_delay().clean_gmc_pool()
        self.with_delay().clean_mail_tracking()
        self.with_delay().clean_partner_communication()
        return True

    def clean_mail_message(self):
        # Clean messages not related to an existing object
        _logger.info("Database cleanup for Compassion Switzerland started")
        self.env.cr.execute("DELETE FROM mail_message WHERE model IS NULL")

        self.env.cr.execute(sql.SQL("SELECT DISTINCT model FROM mail_message"))
        models = [m[0] for m in self.env.cr.fetchall()]

        for model in models:
            table = model.replace(".", "_")
            try:
                # sql libraries do avoid SQL injection, plus this code
                # does not take user input.
                # pylint: disable=sql-injection
                self.env.cr.execute(
                    sql.SQL(
                        "DELETE FROM mail_message WHERE model=%s AND NOT EXISTS ("
                        "    SELECT 1 FROM {} WHERE id = res_id);"
                    ).format(sql.Identifier(table)),
                    [model],
                )
                # Commit the cleanup
                count = self.env.cr.rowcount
                self.env.cr.commit()  # pylint: disable=invalid-commit
                _logger.info(
                    "{} mail_message for invalid {} objects removed".format(
                        count, model
                    )
                )
            except ProgrammingError:
                self.env.cr.rollback()

        # Delete old messages for old objects not useful
        today = date.today()
        limit = today - relativedelta(years=1)
        limit_str = limit.strftime("%Y-%m-%d")

        if "account.invoice" in self.env:
            self.env.cr.execute(
                "DELETE FROM mail_message WHERE model = 'account.invoice' "
                "AND res_id IN (SELECT id FROM account_invoice WHERE state IN ("
                "'cancel', 'paid') AND date_invoice < %s "
                "ORDER BY date_invoice LIMIT 1000)",
                [limit_str],
            )
            count = self.env.cr.rowcount
            self.env.cr.commit()  # pylint: disable=invalid-commit
            _logger.info("{} old invoice messages removed".format(count))

        if "gmc.message" in self.env:
            self.env.cr.execute(
                "DELETE FROM mail_message WHERE model='gmc.message' AND "
                "res_id IN (SELECT id FROM gmc_message WHERE state ="
                "'success' ORDER BY date LIMIT 1000)"
            )
            count = self.env.cr.rowcount
            self.env.cr.commit()  # pylint: disable=invalid-commit
            _logger.info("{} old gmc_pool messages removed".format(count))

        if "partner.communication.job" in self.env:
            self.env.cr.execute(
                "DELETE FROM mail_message WHERE model='partner.communication.job' "
                "AND res_id IN (SELECT id FROM partner_communication_job WHERE "
                "state != 'pending' AND sent_date < %s "
                "ORDER BY sent_date LIMIT 1000)",
                [limit_str],
            )
            count = self.env.cr.rowcount
            self.env.cr.commit()  # pylint: disable=invalid-commit
            _logger.info("{} old partner_communication messages removed".format(count))

        if "correspondence" in self.env:
            self.env.cr.execute(
                "DELETE FROM mail_message WHERE model='correspondence' AND "
                "res_id IN (SELECT id FROM correspondence WHERE "
                "state IN ('Printed and sent to ICP', 'Published to Global Partner') "
                "AND status_date < %s "
                "ORDER BY status_date LIMIT 1000)",
                [limit_str],
            )
            count = self.env.cr.rowcount
            self.env.cr.commit()  # pylint: disable=invalid-commit
            _logger.info("{} old partner_communication messages removed".format(count))

        if "recurring.contract" in self.env:
            self.env.cr.execute(
                "DELETE FROM mail_message WHERE model='recurring.contract' AND "
                "res_id IN (SELECT id FROM recurring_contract WHERE "
                "state IN ('terminated', 'cancelled') AND end_date < %s)",
                [limit_str],
            )
            count = self.env.cr.rowcount
            self.env.cr.commit()  # pylint: disable=invalid-commit
            _logger.info("{} old recurring_contract messages removed".format(count))

        if "account.analytic.account" in self.env:
            self.env.cr.execute(
                "DELETE FROM mail_message WHERE model='account.analytic.account' "
                "AND date < %s",
                [limit_str],
            )
            count = self.env.cr.rowcount
            self.env.cr.commit()  # pylint: disable=invalid-commit
            _logger.info("{} old analytic_account messages removed".format(count))

    def clean_gmc_pool(self):
        old_limit = date.today() - relativedelta(years=3)
        old_messages = self.env["gmc.message"].search(
            [("state", "=", "success"), ("date", "<", old_limit)],
            limit=5000,
            order="date asc",
        )
        old_messages.unlink()
        _logger.info("{} old gmc_pool messages removed".format(len(old_messages)))

    def clean_mail_tracking(self):
        old_limit = date.today() - relativedelta(years=3)
        tracking_values = self.env["mail.tracking.value"].search(
            [("create_date", "<", old_limit)], limit=100000, order="create_date asc"
        )
        tracking_values.unlink()
        _logger.info("{} old mail_tracking values removed".format(len(tracking_values)))
        tracking_events = self.env["mail.tracking.event"].search(
            [("date", "<", old_limit)], limit=100000, order="date asc"
        )
        tracking_events.unlink()
        _logger.info("{} old mail_tracking events removed".format(len(tracking_events)))

    def clean_partner_communication(self):
        old_limit = date.today() - relativedelta(years=3)
        default_communication = self.env.ref(
            "partner_communication.default_communication"
        )
        phonecall = self.env.ref("partner_communication.phonecall_communication")
        excluded_ids = [default_communication.id, phonecall.id]
        old_messages = self.env["partner.communication.job"].search([
            ("state", "!=", "pending"),
            ("date", "<", old_limit),
            ("config_id", "not in", excluded_ids),
            ("body_html", "!=", False),
        ],
            limit=100000,
            order="date asc",
        )
        old_messages.write({"body_html": False})
        _logger.info("{} old partner_communication messages cleaned".format(len(old_messages)))
