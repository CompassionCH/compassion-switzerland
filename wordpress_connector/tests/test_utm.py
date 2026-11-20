##############################################################################
#
#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestWordpressUtm(TransactionCase):
    """UTM of the donations sent by WordPress."""

    def test_empty_utm_is_none(self):
        move = self.env["account.move"]
        source_obj = self.env["utm.source"]
        # a source without name, as the one the empty name used to match
        self.env.cr.execute(
            "INSERT INTO utm_source (name, create_date, write_date) "
            "VALUES ('', now(), now())"
        )
        for empty in ("", "  ", False, None):
            self.assertFalse(move._find_utm("utm.source", empty))
            self.assertFalse(move._find_utm("utm.campaign", empty))
            self.assertFalse(move._find_utm("utm.medium", empty))
        source = source_obj.create({"name": "WordPress test source"})
        self.assertEqual(
            move._find_utm("utm.source", " WordPress test source "), source
        )
        self.assertFalse(move._find_utm("utm.source", "WordPress unknown source"))
