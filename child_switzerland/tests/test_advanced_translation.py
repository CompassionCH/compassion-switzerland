from odoo.tests.common import SingleTransactionCase


class AdvancedTranslationTest(SingleTransactionCase):

    @classmethod
    def setUpClass(cls):
        """ Create test data."""
        super().setUpClass()

        cls.test_partner_obj = cls.env['res.partner']

        tang = cls.browse_ref(cls, 'base.res_partner_address_1')
        joseph = cls.browse_ref(cls, 'base.res_partner_address_2')
        julia = cls.browse_ref(cls, 'base.res_partner_address_26')
        jessica = cls.browse_ref(cls, 'base.res_partner_address_14')
        (julia + jessica).write({'gender': 'F'})

        cls.partner = tang
        cls.partners = tang + joseph + julia + jessica

    def test_get_date(self):
        self.partner.create_date = '2020-01-02 12:30:59'

        tests = [
            ("de_DE", 'date_short', '2.1.2020'),
            ("fr_CH", 'date_short', '2.1.2020'),

            ("fr_CH", 'date_month', '2 janvier'),
            ("de_DE", 'date_month', '2. Januar'),

            ("de_DE", 'date_full', '2. Januar 2020'),
            ("it_IT", 'date_full', '2 gennaio 2020')
        ]
        for lang, arg, expected in tests:
            partner = self.partner.with_context(lang=lang)
            self.assertEquals(partner.get_date('create_date', arg), expected)

    def test_multiple_get_date(self):
        partners = self.partners
        partners[0].create_date = '2020-01-02 12:34:45'
        partners[1].create_date = '2020-01-01 12:34:56'  # should be sorted
        partners[2].create_date = '2020-02-01 12:34:56'  # comma separated
        partners[3].create_date = '2020-02-02 12:34:56'  # 'and' key word

        res = partners.with_context(lang='fr_CH').get_date('create_date', 'date_month')
        self.assertEquals(res, "1 janvier, 2 janvier, 1 février et 2 février")
