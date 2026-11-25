from odoo.tests.common import TransactionCase

from ..models.advocate_details import ENGAGEMENT_FLAG_XMLIDS


class TestAdvocateEngagementFlags(TransactionCase):
    """One yes/no column per main engagement type, so that an export of the
    advocates gives one line per advocate (T2740)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.engagement = {
            field: cls.env.ref(xmlid) for field, xmlid in ENGAGEMENT_FLAG_XMLIDS.items()
        }
        partner = cls.env["res.partner"].create({"name": "Volunteer Test"})
        cls.advocate = cls.env["advocate.details"].create(
            {
                "partner_id": partner.id,
                "engagement_ids": [
                    (
                        6,
                        0,
                        (
                            cls.engagement["engaged_sport"]
                            | cls.engagement["engaged_prayer"]
                            | cls.engagement["engaged_translation"]
                        ).ids,
                    )
                ],
            }
        )

    def _flags(self):
        return {field: self.advocate[field] for field in ENGAGEMENT_FLAG_XMLIDS}

    def test_one_column_per_engagement(self):
        self.assertEqual(
            self._flags(),
            {
                "engaged_events": False,
                "engaged_sport": True,
                "engaged_prayer": True,
                "engaged_translation": True,
                "engaged_church_presentation": False,
                "engaged_church_advocate": False,
                "engaged_office_volunteer": False,
            },
        )

    def test_columns_follow_the_engagements(self):
        self.advocate.engagement_ids = [
            (3, self.engagement["engaged_sport"].id),
            (4, self.engagement["engaged_church_advocate"].id),
        ]
        flags = self._flags()
        self.assertFalse(flags["engaged_sport"])
        self.assertTrue(flags["engaged_church_advocate"])
        self.assertTrue(flags["engaged_prayer"])

    def test_export_gives_one_line_per_advocate(self):
        # The export dialog by default, "import-compatible export" unticked
        advocate = self.advocate.with_context(import_compat=False)
        fields_to_export = ["partner_id", *ENGAGEMENT_FLAG_XMLIDS]
        rows = advocate.export_data(fields_to_export)["datas"]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][1:], [False, True, True, True, False, False, False])
        # The many2many itself is what adds a line per extra engagement
        rows = advocate.export_data(["partner_id", "engagement_ids"])["datas"]
        self.assertEqual(len(rows), 3)
