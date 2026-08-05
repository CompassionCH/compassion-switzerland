##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: David Coninckx <david@coninckx.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging
from datetime import date

from dateutil.relativedelta import relativedelta
from psycopg2 import OperationalError

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.service.model import PG_CONCURRENCY_ERRORS_TO_RETRY

from odoo.addons.child_compassion.models.compassion_hold import HoldType

from ..tools.wp_sync import WPSync

logger = logging.getLogger(__name__)


class CompassionChild(models.Model):
    _inherit = "compassion.child"

    state = fields.Selection(
        selection_add=[("I", "On Wordpress")],
        ondelete={"I": lambda c: c.write({"state": "N"})},
    )

    def _available_states(self):
        res = super()._available_states()
        res.append("I")
        return res

    def add_to_wordpress(self, company_id=None, wp=None):
        in_two_years = date.today() + relativedelta(years=2)
        valid_children = self.filtered(
            lambda c: c.state == "N"
            and c.description_de
            and c.description_fr
            and c.description_it
            and c.project_id.description_fr
            and c.project_id.description_de
            and c.project_id.description_it
            and c.fullshot
            and (not c.completion_date or c.completion_date > in_two_years)
        )

        error = self - valid_children
        if error:
            number = str(len(error))
            logger.error(
                f"{number} children have invalid data and were not pushed "
                f"to wordpress"
            )

        if not valid_children:
            return 0, 0

        if wp is None:
            wp_config = self.env["wordpress.configuration"].get_config(company_id)
            wp = WPSync(wp_config)

        success_count = wp.upload_children(valid_children)

        return success_count or 0, len(valid_children)

    def remove_from_wordpress(self):
        try:
            valid_children = self.filtered(lambda c: c.state == "I")
            if valid_children:
                wp_config = self.env["wordpress.configuration"].get_config()
                wp = WPSync(wp_config)
                if wp.remove_children(valid_children):
                    valid_children.write({"state": "N"})
            return True
        except Exception as e:
            logger.error(f"Error removing children from WordPress: {e}", exc_info=True)
            raise

    def force_remove_from_wordpress(self, company_id=None, wp=None):
        try:
            if wp is None:
                wp_config = self.env["wordpress.configuration"].get_config(company_id)
                wp = WPSync(wp_config)
            if wp.remove_all_children():
                logger.info("ALL CHILDREN REMOVED")
                self.with_delay(channel="root.child_compassion").write({"state": "N"})
            return True
        except Exception as e:
            logger.error(
                f"Error force removing children from WordPress: {e}",
                exc_info=True,
            )
            raise

    def child_sponsored(self, sponsor_id):
        """Remove children from the website when they are sponsored."""
        if self.state == "I":
            self.remove_from_wordpress()
        return super().child_sponsored(sponsor_id)

    def child_released(self, state="R"):
        """Remove from typo3 when child is released"""
        to_remove_from_web = self.filtered(lambda c: c.state == "I")
        if to_remove_from_web:
            to_remove_from_web.remove_from_wordpress()

        return super().child_released(state)

    @api.model
    def refresh_wordpress_cron(self):
        """
        Find new children on the global childpool, put them on wordpress,
        remove old children and release the holds.
        :return: True
        """
        # Fetch the "Number Children Website" setting from the database
        settings = (
            self.env["res.config.settings"].sudo().search([], order="id DESC", limit=1)
        )
        take = (
            settings.number_children_website
            if settings and settings.number_children_website
            else 120
        )

        for company in self.env["res.company"].search([]):
            wp_config = self.env["wordpress.configuration"].get_config(
                company.id, raise_error=False
            )
            if not wp_config:
                continue
            global_pool = self.with_company(company.id)._create_diverse_children_pool(
                int(take)
            )
            self.with_delay_sh(
                "_hold_and_push_to_wordpress",
                company.id,
                global_pool,
                channel="root.child_compassion",
                description="Hold and push children to wordpress",
            )
        return True

    def _create_diverse_children_pool(self, take):
        global_pool = self.env["compassion.childpool.search"].create(
            {
                "take": take,
            }
        )
        try:
            global_pool.country_mix()
        except UserError:
            logger.error(
                "The country-aware children selection failed, "
                "falling back to rich mix.",
                exc_info=True,
            )
            global_pool.rich_mix()
        return global_pool

    def _hold_and_push_to_wordpress(self, company_id, global_pool):
        try:
            new_children = self._hold_children(global_pool)
            valid_new_children = new_children._update_information_and_filter_invalid()
            old_children = self.search(
                [
                    ("state", "=", "I"),
                    ("hold_id.type", "!=", HoldType.NO_MONEY_HOLD.value),
                ]
            )
            self._replace_children_in_wordpress(
                company_id, old_children, valid_new_children
            )
        except Exception as e:
            if (
                isinstance(e, OperationalError)
                and e.pgcode in PG_CONCURRENCY_ERRORS_TO_RETRY
            ):
                # Transient conflict with a concurrent write: queue_job
                # retries the job, no need to alert the developer.
                raise
            logger.error("Critical failure in WordPress sync job", exc_info=True)
            with self.pool.cursor() as cr:
                env = api.Environment(cr, self.env.uid, self.env.context)
                self.with_env(env).with_company(company_id)._notify_developer(
                    f"The WordPress Sync background job crashed: {str(e)}"
                )
            raise

    def _update_information_and_filter_invalid(self):
        for child in self:
            try:
                child.get_infos()
                child.mapped("project_id").update_informations()
            except Exception:
                logger.error(
                    f"Error updating child information for {child.id} ", exc_info=True
                )
                continue

        return self.filtered(
            lambda c: c.state == "N"
            and c.description_it
            and c.pictures_ids
            and c.project_id.description_it
        )

    def _hold_children(self, global_pool):
        hold_wizard = (
            global_pool.env["child.hold.wizard"]
            .with_context(active_id=global_pool.id, queue_job__no_delay=True)
            .create(
                {
                    "type": HoldType.CONSIGNMENT_HOLD.value,
                    "expiration_date": self.env[
                        "compassion.hold"
                    ].get_default_hold_expiration(HoldType.CONSIGNMENT_HOLD),
                    "primary_owner": 1,
                    "channel": "web",
                }
            )
        )
        hold_wizard.onchange_type()
        send_hold_result = hold_wizard.send()
        children = self.browse(send_hold_result["domain"][0][2]).with_context(
            queue_job__no_delay=True
        )
        return children

    def _replace_children_in_wordpress(self, company_id, old_children, new_children):
        # Initiate WPSync once
        wp_config = self.env["wordpress.configuration"].get_config(
            company_id, raise_error=False
        )
        if not wp_config:
            raise UserError(f"Missing WP Config for company {company_id}")

        try:
            wp = WPSync(wp_config)
        except Exception as e:
            raise UserError(
                f"Failed to authenticate WPSync before batching: {e}"
            ) from e

        try:
            with self.env.cr.savepoint():
                old_children.force_remove_from_wordpress(
                    company_id=company_id,
                    wp=wp,
                )
        except Exception as e:
            raise UserError(
                f"Error force removing old children from WordPress: {e}"
            ) from e

        # Save points after each batch
        # Put children 5 by 5 to avoid delays
        total_uploaded = 0
        total_expected = 0
        failed_batches = 0
        for i in range(0, len(new_children), 5):
            try:
                with self.env.cr.savepoint():
                    success_count, valid_count = new_children[
                        i : i + 5
                    ].add_to_wordpress(company_id=company_id, wp=wp)
                    total_uploaded += success_count
                    total_expected += valid_count
                    if success_count < valid_count:
                        logger.warning(
                            f"Batch {i} partial success: "
                            f"{success_count}/{valid_count}"
                        )
            except Exception:
                logger.error(
                    "Failed adding a batch of children to wordpress: ",
                    exc_info=True,
                )
                failed_batches += 1
                continue

        if failed_batches > 0 or total_uploaded < total_expected:
            warning_msg = (
                f"Sync completed with issues: {failed_batches} failed batches, "
                f"{total_uploaded}/{total_expected} children uploaded."
            )
            logger.warning(warning_msg)

            # Send the email with partial failure
            with self.pool.cursor() as cr:
                env = api.Environment(cr, self.env.uid, self.env.context)
                self.with_env(env).with_company(company_id)._notify_developer(
                    warning_msg
                )

        # Release holds
        try:
            with self.env.cr.savepoint():
                old_children.mapped("hold_id").release_hold()
        except Exception:
            logger.error("Error when refreshing wordpress children.")

    def _notify_developer(self, message: str) -> None:
        """
        Sends an email to the IT team regarding child a child sync issue
        """

        dev_email = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("child_wp.developer_email", "it@compassion.ch")
        )

        mail_values = {
            "subject": "[URGENT] Odoo -> WordPress Sync Failure",
            "body_html": f"""
            <p>Hello Team,</p>
            <p>The odoo scheduled action for syncing children to
            WordPress has encountered a failure.</p>
            <p><b>Error details:</b></p>
            <pre>{message}</pre>
            <p>Please trigger the job manually and resolve the problem ASAP!</p>
            <br/>
            <p><i>Thanks for your work & God bless you!</i></p>
            """,
            "email_to": dev_email,
            "email_from": self.env.company.email or "noreply@compassion.ch",
            "state": "outgoing",
            "author_id": False,
        }

        try:
            mail = self.env["mail.mail"].sudo().create(mail_values)
            mail.send()
        except Exception:
            logger.error("Failed to send developer notification email.", exc_info=True)
