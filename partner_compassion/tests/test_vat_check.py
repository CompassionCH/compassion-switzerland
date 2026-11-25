from unittest import SkipTest

from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestVatCheck(TransactionCase):
    """T3693 The Tax ID is only checked when it is changed"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner_model = cls.env["res.partner"]
        if "check_vat_ch" not in dir(cls.partner_model):
            raise SkipTest("base_vat is not installed")
        cls.switzerland = cls.env.ref("base.ch")
        cls.belgium = cls.env.ref("base.be")
        # An old Tax ID that is not a valid VAT number
        cls.partner = (
            cls.partner_model.with_context(no_vat_validation=True)
            .create(
                {
                    "name": "T3693 Contact",
                    "country_id": cls.switzerland.id,
                    "vat": "15.420.67",
                }
            )
            .with_env(cls.env)
        )

    def test_address_change_with_old_tax_id(self):
        self.partner.write({"country_id": self.belgium.id, "city": "Bruxelles"})
        self.partner.write({"country_id": self.switzerland.id, "zip": "2000"})
        self.assertEqual(self.partner.country_id, self.switzerland)
        self.assertEqual(self.partner.vat, "15.420.67")

    def test_new_invalid_tax_id_refused(self):
        with self.assertRaises(ValidationError):
            self.partner.write({"vat": "12.345.67"})

    def test_new_invalid_tax_id_with_country_refused(self):
        with self.assertRaises(ValidationError):
            self.partner.write({"vat": "12.345.67", "country_id": self.belgium.id})

    def test_new_invalid_tax_id_on_child_refused(self):
        """A Tax ID changed through another contact's save is checked"""
        child = self.partner_model.create(
            {"name": "T3693 Child", "is_company": True, "parent_id": self.partner.id}
        )
        with self.assertRaises(ValidationError):
            self.partner.write(
                {"child_ids": [(1, child.id, {"vat": "12.345.67"})], "city": "Bern"}
            )

    def test_new_contact_with_invalid_tax_id_refused(self):
        """A contact created through another contact's save is checked"""
        with self.assertRaises(ValidationError):
            self.partner.write(
                {
                    "child_ids": [
                        (
                            0,
                            0,
                            {
                                "name": "T3693 New child",
                                "is_company": True,
                                "country_id": self.switzerland.id,
                                "vat": "12.345.67",
                            },
                        )
                    ],
                    "city": "Bern",
                }
            )

    def test_valid_tax_id_accepted(self):
        self.partner.write({"vat": "CHE-100.000.006 MWST"})
        self.assertEqual(self.partner.vat, "CHE-100.000.006 MWST")
