import json

from lxml import etree

from odoo import api, models


class IrUiView(models.Model):
    _inherit = "ir.ui.view"

    @api.model
    def _remove_footer_call_to_action(self):
        """Remove the "Get involved now" blocks from the website copies of the
        Compassion CH footer, in every language, and keep space above the
        copyright that now starts the footer (T3599). The copies were edited in
        the website editor, so the template doesn't update them. Does nothing
        once removed.
        """
        views = self.with_context(active_test=False).search(
            [("key", "=", "website_switzerland.footer")]
        )
        for view in views:
            self.env.cr.execute(
                "SELECT arch_db FROM ir_ui_view WHERE id = %s", (view.id,)
            )
            arch_by_lang = self.env.cr.fetchone()[0] or {}
            new_arch_by_lang = {}
            for lang, arch in arch_by_lang.items():
                root = etree.fromstring(arch)
                blocks = root.xpath("//section[@data-name='Call to Action']")
                if not blocks:
                    continue
                separator = blocks[-1].getnext()
                for block in blocks:
                    block.getparent().remove(block)
                if (
                    separator is not None
                    and "pt48" not in separator.get("class", "").split()
                ):
                    separator.set("class", f"{separator.get('class', '')} pt48".strip())
                new_arch_by_lang[lang] = etree.tostring(root, encoding="unicode")
            if new_arch_by_lang:
                self.env.cr.execute(
                    "UPDATE ir_ui_view SET arch_db = arch_db || %s::jsonb"
                    " WHERE id = %s",
                    (json.dumps(new_arch_by_lang), view.id),
                )
                view.invalidate_recordset(["arch_db", "arch"])
