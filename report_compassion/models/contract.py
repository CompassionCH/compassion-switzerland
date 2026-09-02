##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from markupsafe import Markup

from odoo import api, fields, models


class AccountInvoice(models.Model):
    """
    Make Invoice translatable for communications with dates.
    """

    _inherit = ["account.move", "translatable.model"]
    _name = "account.move"

    # Gender field is mandatory for translatable models
    gender = fields.Char(compute="_compute_gender")

    def _compute_gender(self):
        for i in self:
            i.gender = "M"


class Contract(models.Model):
    _inherit = "recurring.contract"

    def get_gift_communication(self, product, plain=False):
        """
        :param plain: return a single-line, comma-separated plain string
        instead of a <br/>-separated Markup, for contexts (e.g. the printed
        BVR communication line) that can't render real HTML - building it
        directly from the unescaped parts avoids round-tripping the Markup
        value through escape/unescape.
        """
        self.ensure_one()
        lang = self.mapped(self.send_gifts_to).lang
        child = self.child_id.with_context(lang=lang)
        born = {
            "en_US": "Born in",
            "fr_CH": "Né le" if child.gender == "M" else "Née le",
            "de_DE": "Geburtstag",
            "it_IT": "Compleanno",
        }
        birthdate = child.birthdate.strftime("%d.%m.%Y")
        vals = {
            "firstname": child.preferred_name,
            "local_id": child.local_id,
            "product": product.with_context(lang=lang).name,
            "birthdate": born[lang] + " " + birthdate
            if "Birthday" in product.with_context(lang="en_US").name
            else "",
        }
        if "Birthday" in product.with_context(lang="en_US").name:
            parts = [
                f"{vals['firstname']} ({vals['local_id']})",
                f"{vals['product']}",
                f"{vals['birthdate']}",
            ]
        else:
            parts = [f"{vals['firstname']} ({vals['local_id']})", f"{vals['product']}"]
        sep = ", " if plain else Markup("<br/>")
        communication = sep.join(parts)
        gift_threshold = self.env["gift.threshold.settings"].search(
            [("product_id", "=", product.id)], limit=1
        )
        if gift_threshold:
            min_amount = int(gift_threshold.min_amount)
            max_amount = int(gift_threshold.max_amount)
            amount_limit = {
                "en_US": f"CHF {min_amount}.- to max {max_amount}.- per year",
                "fr_CH": f"CHF {min_amount}.- à max. {max_amount}.- par année",
                "de_DE": f"CHF {min_amount}.- bis max. {max_amount}.- pro Jahr",
                "it_IT": f"Importo tra CHF {min_amount}.- e {max_amount}.- per anno",
            }
            communication += sep + f"{amount_limit[lang]}"
        return communication

    @api.model
    def get_sponsorship_gift_products(self):
        gift_categ_id = self.env.ref("sponsorship_compassion.product_category_gift").id
        return self.env["product.product"].search(
            [
                ("categ_id", "=", gift_categ_id),
                ("sponsorship_gift_type_id", "!=", False),
            ]
        )
