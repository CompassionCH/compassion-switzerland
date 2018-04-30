# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Stephane Eicher <seicher@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import fields
from odoo.addons.sponsorship_compassion.tests.test_sponsorship_compassion \
    import BaseSponsorshipTest
import logging
import simplejson
import mock
logger = logging.getLogger(__name__)


mock_project_infos = ('odoo.addons.child_compassion.models.project_compassion'
                      '.CompassionProject.update_informations')
mock_get_infos = ('odoo.addons.child_compassion.models.child_compassion'
                  '.CompassionChild.get_infos')
mock_update_hold = ('odoo.addons.child_compassion.models.compassion_hold'
                    '.CompassionHold.update_hold')
mock_get_staff = ('odoo.addons.child_compassion.wizards'
                  '.staff_notification_settings.StaffNotificationSettings'
                  '.get_param')
mock_new_dossier = ('odoo.addons.partner_communication_switzerland.models'
                    '.contracts.RecurringContract._new_dossier')


class TestWordpressConnector(BaseSponsorshipTest):

    def setUp(self):
        self.form_data = {
            'city': 'MyCity',
            'first_name': 'TestFirstName',
            'last_name': 'TestLastName',
            'language': ['französich', 'englisch'],
            'zahlungsweise': 'dauerauftrag',
            'consumer_source_text': 'Times Magazine',
            'zipcode': '1000',
            'birthday': '01/01/1923',
            'Beruf': 'Agriculteur paysan',
            'phone': '021 345 67 89',
            'consumer_source': 'Anzeige in Zeitschrift',
            'street': 'Rue test 1',
            'kirchgemeinde': u'Mon église',
            'mithelfen': {
                'checkbox': 'on'
            },
            'salutation': 'Herr',
            'patenschaftplus': {
                'checkbox': 'on'
            },
            'email': 'email@compassion.ch',
            'childID': u'15783',
            'land': 'Suisse'
        }
        self.utm_source = 'Search engine'
        super(TestWordpressConnector, self).setUp()

    @mock.patch(mock_new_dossier)
    @mock.patch(mock_update_hold)
    @mock.patch(mock_get_infos)
    @mock.patch(mock_project_infos)
    def add_active_sponsorship(self, partner, child_local_id, project_infos,
                               get_infos, update_hold, new_dossiers):
        project_infos.return_value = True
        get_infos.return_value = True
        update_hold.return_value = True
        new_dossiers.return_value = True
        child_sponsored = self.create_child(child_local_id)
        sp_group = self.create_group({
            'change_method': 'do_nothing',
            'partner_id': partner.id,
            'advance_billing_months': 1,
            'payment_mode_id': self.payment_mode.id
        })
        sponsorship = self.create_contract({
            'child_id': child_sponsored.id,
            'group_id': sp_group.id,
            'partner_id': partner.id
        },
            [{'amount': 50.0}]
        )
        self.validate_sponsorship(sponsorship)
        super(TestWordpressConnector, self).pay_sponsorship(sponsorship)
        return sponsorship, child_sponsored

    def create_sponsorship_default(self, child_local_id, form_data=None,
                                   lang='fr', utm_source=None,
                                   utm_medium="Website",
                                   utm_campaign="Newsletter"):
        if not form_data:
            form_data = self.form_data
        if not utm_source:
            utm_source = self.utm_source
        return self.env['recurring.contract']. \
            create_sponsorship(child_local_id, form_data, lang, utm_source,
                               utm_medium, utm_campaign)

    def check_sponsorship(self, s, child, utm_source=None,
                          fully_managed=True, is_active=False,
                          user_id=False, origin_id=False, partner_id=False):
        self.assertEqual(s.child_id, child)
        self.assertEqual(s.child_code, child.local_id)
        self.assertEqual(s.state, 'draft')
        self.assertEqual(s.source_id.name, utm_source or self.utm_source)
        self.assertEqual(s.next_invoice_date, fields.Date.today())
        self.assertEqual(s.fully_managed, fully_managed)
        self.assertEqual(s.is_active, is_active)
        self.assertEqual(s.user_id.id, user_id)
        self.assertEqual(s.origin_id.id, origin_id)
        self.assertEqual(s.partner_id.id, partner_id)

    @mock.patch(mock_get_staff)
    def test_missing_partner(self, get_staff):
        get_staff.return_value = [2]
        child = self.create_child('UG1239181')

        sponsorship_res = self.create_sponsorship_default(child.local_id)
        self.assertTrue(sponsorship_res)

        s = self.env['recurring.contract'].search([
            ('web_data', '=', simplejson.dumps(self.form_data))], limit=1)
        self.check_sponsorship(s, child)
        self.assertTrue(s.unlink())

    @mock.patch(mock_get_staff)
    @mock.patch(mock_update_hold)
    @mock.patch(mock_get_infos)
    @mock.patch(mock_project_infos)
    def test_existing_partner(self, project_infos, get_infos, update_hold,
                              get_staff):
        project_infos.return_value = True
        get_infos.return_value = True
        update_hold.return_value = True
        get_staff.return_value = [2]
        child = self.create_child('UG4239181')
        michel_form_data = self.form_data.copy()
        michel_form_data.update({
            'first_name': self.michel.firstname,
            'last_name': self.michel.lastname,
            'zipcode': self.michel.zip,
            'city': 'Big Apple'
        })

        sponsorship_res = self.create_sponsorship_default(
            child.local_id, form_data=michel_form_data)
        self.assertTrue(sponsorship_res)

        s = self.env['recurring.contract'].search([
            ('web_data', '=', simplejson.dumps(michel_form_data))], limit=1)
        self.check_sponsorship(s, child, partner_id=self.michel.id)
        self.assertTrue(child.unlink)
        self.assertTrue(s.unlink)

    @mock.patch(mock_get_staff)
    def test_duplicate_partner_no_sponsorship(self, get_staff):
        get_staff.return_value = [2]
        # creating duplicate of michel
        duplicate_michel = self.env['res.partner'].create({
            'firstname': self.michel.firstname,
            'lastname': self.michel.lastname,
            'zip': self.michel.zip,
            'city': 'Big city',
        })
        child = self.create_child('UG1119182')

        michel_form_data = self.form_data.copy()
        michel_form_data.update({
            'first_name': self.michel.firstname,
            'last_name': self.michel.lastname,
            'zipcode': self.michel.zip,
            'city': 'Yverdon',
        })

        sponsorship_res = self.create_sponsorship_default(
            child.local_id, form_data=michel_form_data)
        self.assertTrue(sponsorship_res)

        s = self.env['recurring.contract'].search([
            ('web_data', '=', simplejson.dumps(michel_form_data))], limit=1)
        self.check_sponsorship(s, child)
        self.assertTrue(s.unlink)
        self.assertTrue(child.unlink)
        self.assertTrue(duplicate_michel.unlink())

    @mock.patch(mock_get_infos)
    @mock.patch(mock_project_infos)
    @mock.patch(mock_update_hold)
    @mock.patch(mock_get_staff)
    def test_duplicate_partner_one_sponsorship(self, get_staff, update_hold,
                                               project_infos, get_infos):
        get_staff.return_value = [2]
        update_hold.return_value = True
        project_infos.return_value = True
        get_infos.return_value = True
        # creating duplicate of michel
        duplicate_michel = self.env['res.partner'].create({
            'firstname': self.michel.firstname,
            'lastname': self.michel.lastname,
            'zip': self.michel.zip,
            'city': 'Nice city'
        })
        child = self.create_child('UG1839182')
        self.add_active_sponsorship(
            self.michel, 'UG182891')
        michel_form_data = self.form_data.copy()
        michel_form_data.update({
            'first_name': self.michel.firstname,
            'last_name': self.michel.lastname,
            'zipcode': self.michel.zip,
            'city': 'Kairo'
        })

        sponsorship_res = self.create_sponsorship_default(
            child.local_id, form_data=michel_form_data)
        self.assertTrue(sponsorship_res)

        s = self.env['recurring.contract'].search([
            ('web_data', '=', simplejson.dumps(michel_form_data))], limit=1)
        self.check_sponsorship(s, child, partner_id=self.michel.id)
        self.assertTrue(s.unlink())
        self.assertTrue(child.unlink())
        self.assertTrue(duplicate_michel.unlink())

    @mock.patch(mock_update_hold)
    @mock.patch(mock_get_staff)
    def test_duplicate_partner_two_sponsorships(self, get_staff, update_hold):
        get_staff.return_value = [2]
        update_hold.return_value = True
        # creating duplicate of michel
        duplicate_michel = self.env['res.partner'].create({
            'firstname': self.michel.firstname,
            'lastname': self.michel.lastname,
            'zip': self.michel.zip,
            'city': 'Vladi'
        })
        child = self.create_child('UG1859182')
        self.add_active_sponsorship(self.michel, 'UG152891')
        self.add_active_sponsorship(duplicate_michel, 'UG582891')

        michel_form_data = self.form_data.copy()
        michel_form_data.update({
            'first_name': self.michel.firstname,
            'last_name': self.michel.lastname,
            'zipcode': self.michel.zip,
            'city': 'Wadi'
        })

        sponsorship_res = self.create_sponsorship_default(
            child.local_id, form_data=michel_form_data)
        self.assertTrue(sponsorship_res)

        s = self.env['recurring.contract'].search([
            ('web_data', '=', simplejson.dumps(michel_form_data))], limit=1)
        self.check_sponsorship(s, child)

    @mock.patch(mock_update_hold)
    @mock.patch(mock_get_staff)
    def test_muskathlon(self, get_staff, update_hold):
        get_staff.return_value = [2]
        update_hold.return_value = True

        event = self.env['crm.event.compassion'].create({
            'name': "Muskathlon Test",
            'type': 'sport',
            'number_allocate_children': 2,
            'planned_sponsorships': 12,
            'start_date': fields.Date.today(),
            'end_date': fields.Date.today(),
            'hold_start_date': fields.Date.today(),
            'hold_end_date': fields.Date.today(),
        })
        # origin = self.env['recurring.contract.origin'].create({
        #    'type': 'event',
        #    'event_id': event.id
        # })

        michel_form_data = self.form_data.copy()
        michel_form_data.update({
            'first_name': self.michel.firstname,
            'last_name': self.michel.lastname,
            'zipcode': self.michel.zip,
            'city': 'Big Apple',
            'consumer_source': 'msk' + str(event.id) + '_Muskathlon',
            'consumer_source_text': 'msk' + str(self.thomas.id) +
                                    '_FirstnameLastName'
        })

        child = self.create_child('UG1a51182')
        sponsorship_res = self.create_sponsorship_default(
            child.local_id, form_data=michel_form_data)
        self.assertTrue(sponsorship_res)

        s = self.env['recurring.contract'].search([
            ('web_data', '=', simplejson.dumps(michel_form_data))], limit=1)
        self.check_sponsorship(s, child, user_id=self.thomas.id,
                               partner_id=self.michel.id)
