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

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools import relativedelta

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

    def add_to_wordpress(self, company_id=None):
        in_two_years = date.today() + relativedelta(years=2)
        valid_children = self.filtered(
            lambda c: c.state == "N"
            and c.desc_de
            and c.desc_fr
            and c.desc_it
            and c.project_id.desc_fr
            and c.project_id.desc_de
            and c.project_id.desc_it
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

        wp_config = self.env["wordpress.configuration"].get_config(company_id)
        wp = WPSync(wp_config)
        return wp.upload_children(valid_children)

    def remove_from_wordpress(self):
        valid_children = self.filtered(lambda c: c.state == "I")
        if valid_children:
            wp_config = self.env["wordpress.configuration"].get_config()
            wp = WPSync(wp_config)
            if wp.remove_children(valid_children):
                valid_children.write({"state": "N"})
        return True

    def force_remove_from_wordpress(self, company_id=None):
        wp_config = self.env["wordpress.configuration"].get_config(company_id)
        wp = WPSync(wp_config)
        if wp.remove_all_children():
            self.write({"state": "N"})
        return True

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
        settings = self.env['res.config.settings'].sudo().search([], order='id DESC', limit=1)
        take = settings.number_children_website if settings and settings.number_children_website else 120

        for company in self.env["res.company"].search([]):
            wp_config = self.env["wordpress.configuration"].get_config(
                company.id, raise_error=False
            )
            if not wp_config:
                continue
            global_pool = self.with_company(company.id)._create_diverse_children_pool(
                int(take)
            )
            new_children = self._hold_children(global_pool)
            valid_new_children = self._update_information_and_filter_invalid(
                new_children
            )
            old_children = self.search(
                [
                    ("state", "=", "I"),
                    ("hold_id.type", "!=", HoldType.NO_MONEY_HOLD.value),
                ]
            )
            self._replace_children_in_wordpress(
                company.id, old_children, valid_new_children
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

    def _update_information_and_filter_invalid(self, children):
        for child in children:
            try:
                child.get_infos()
                child.mapped("project_id").update_informations()
            except UserError:
                logger.error("Error updating child information: ", exc_info=True)
                continue
        return children.filtered(
            lambda c: c.state == "N"
            and c.desc_it
            and c.pictures_ids
            and c.project_id.desc_it
        )

    def _hold_children(self, global_pool):
        hold_wizard = (
            global_pool.env["child.hold.wizard"]
            .with_context(active_id=global_pool.id, async_mode=False)
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
            async_mode=False
        )
        return children

    def _replace_children_in_wordpress(self, company_id, old_children, new_children):
        try:
            with self.env.cr.savepoint():
                old_children.force_remove_from_wordpress(company_id)
                # Put children 5 by 5 to avoid delays
                for i in range(0, len(new_children), 5):
                    try:
                        new_children[i : i + 5].add_to_wordpress(company_id)
                    except Exception:
                        logger.error(
                            "Failed adding a batch of children to" " wordpress: ",
                            exc_info=True,
                        )
                        continue

                old_children.mapped("hold_id").release_hold()
        except Exception:
            logger.error("Error when refreshing wordpress children.")
