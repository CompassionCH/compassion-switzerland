##############################################################################
#
#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo.tests import TransactionCase, tagged

from ..models.utm import find_utm


@tagged("post_install", "-at_install")
class TestWordpressUtm(TransactionCase):
    """UTM of the donations sent by WordPress."""

    def test_empty_utm_is_none(self):
        source_obj = self.env["utm.source"]
        # a source without name, as the one the empty name used to match
        self.env.cr.execute(
            "INSERT INTO utm_source (name, create_date, write_date) "
            "SELECT '', now(), now() "
            "WHERE NOT EXISTS (SELECT 1 FROM utm_source WHERE name = '')"
        )
        for empty in ("", "  ", False, None):
            self.assertFalse(find_utm(self.env, "utm.source", empty))
            self.assertFalse(find_utm(self.env, "utm.campaign", empty))
            self.assertFalse(find_utm(self.env, "utm.medium", empty))
        source = source_obj.create({"name": "WordPress test source"})
        self.assertEqual(
            find_utm(self.env, "utm.source", " WordPress test source "), source
        )
        self.assertFalse(find_utm(self.env, "utm.source", "WordPress unknown source"))
