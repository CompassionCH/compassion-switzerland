##############################################################################
#
#    Copyright (C) 2017 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging
import os
from datetime import date

import mock
from dateutil.relativedelta import relativedelta
from odoo.addons.sponsorship_compassion.tests.test_sponsorship_compassion \
    import BaseSponsorshipTest

from odoo.tools import file_open
from odoo import fields


logger = logging.getLogger(__name__)

mock_update_hold = ('odoo.addons.child_compassion.models.compassion_hold'
                    '.CompassionHold.update_hold')
mock_get_pdf = 'odoo.addons.base_report_to_printer.models' \
               '.ir_actions_report.IrActionsReport.render_qweb_pdf'

mock_force_activation = 'odoo.addons.recurring_contract.models.' \
                        'recurring_contract.RecurringContract.force_activation'

mock_get_infos = 'odoo.addons.child_compassion.models.' \
                        'child_compassion.CompassionChild.get_infos'


class TestSponsorship(BaseSponsorshipTest):

    def setUp(self):
        super().setUp()
        # Deactivate mandates of Michel Fletcher to avoid directly validate
        # sponsorship to waiting state.
        self.thomas.ref = self.ref(7)
        self.michel.ref = self.ref(7)
        self.mandates = self.env['account.banking.mandate'].search([
            ('partner_id', '=', self.michel.parent_id.id)])
        self.mandates.write({'state': 'draft'})
        payment_mode_lsv = self.env.ref(
            'sponsorship_switzerland.payment_mode_lsv')
        self.lsv_group = self.create_group({
            'partner_id': self.michel.id,
            'payment_mode_id': payment_mode_lsv.id,
        })
        self.bvr_group = self.create_group({
            'partner_id': self.thomas.id,
            'payment_mode_id': self.env.ref(
                'sponsorship_switzerland.payment_mode_bvr').id,
        })
        self.is_travis = 'TRAVIS' in os.environ
        self.base_path = 'partner_communication_switzerland/static/src/test.pdf'

    @mock.patch(mock_update_hold)
    @mock.patch(mock_get_pdf)
    def test_welcome_letters_normal(self, get_pdf, update_hold):
        """
        Create a sponsorship, validate it, activate it and test that
        welcome e-mail and welcome active communications are sent on the
        right time.

        Welcome e-mail should be sent 10 days after contract validation
        Welcome active should be sent after activation, at least 5 days after
        contract validation.
        """
        update_hold.return_value = True

        if self.is_travis:
            travis_path = 'addons/' + self.base_path
            with file_open(travis_path, 'rb') as test:
                get_pdf.return_value = test.read()
        else:
            cwd = os.getcwd()
            f_path = cwd + '/compassion-switzerland/' + self.base_path
            with open(f_path, 'rb') as fopen:
                get_pdf.return_value = fopen.read().decode('latin-1')

        # Creation of the sponsorship contract
        child = self.create_child(self.ref(11))
        sponsorship = self.create_contract(
            {
                'partner_id': self.thomas.id,
                'group_id': self.bvr_group.id,
                'child_id': child.id,
            },
            [{'amount': 50.0}]
        )
        self.validate_sponsorship(sponsorship)
        self.assertEqual(sponsorship.sds_state, 'waiting_welcome')
        # Perform action rules (shouldn't do anything)
        self.env['base.automation']._check()
        self.assertEqual(sponsorship.sds_state, 'waiting_welcome')

        # Simulate the SDS state was in 10 days and check the welcome e-mail
        # is sent.
        eleven_days_ago = date.today() - relativedelta(days=11)
        sponsorship.sds_state_date = fields.Date.to_string(eleven_days_ago)
        self.env.ref('partner_communication_switzerland.check_welcome_email') \
            .last_run = fields.Date.to_string(eleven_days_ago)
        sponsorship.send_welcome_letter()
        self.assertEqual(sponsorship.sds_state, 'active')

        # Check the communication is generated after sponsorship validation
        welcome_email = self.env.ref(
            'partner_communication_switzerland.planned_welcome')
        partner_communications = self.env['partner.communication.job'].search([
            ('partner_id', '=', self.thomas.id),
            ('state', '=', 'pending'),
            ('config_id', '=', welcome_email.id)
        ])
        self.assertTrue(partner_communications)

        # Now test the welcome active communication
        sponsorship.force_activation()
        two_days_ago = date.today() - relativedelta(days=2)
        sponsorship.activation_date = fields.Date.to_string(two_days_ago)
        sponsorship._send_welcome_active_letters_for_activated_sponsorships()
        welcome_active = self.env.ref(
            'partner_communication_switzerland.welcome_activation')
        partner_communications = self.env['partner.communication.job'].search([
            ('partner_id', '=', self.thomas.id),
            ('config_id', '=', welcome_active.id)
        ])
        self.assertFalse(partner_communications)
        self.assertFalse(sponsorship.welcome_active_letter_sent)

        # Now set the start date in the past and welcome active should be sent
        sponsorship.start_date = fields.Date.to_string(eleven_days_ago)
        sponsorship._send_welcome_active_letters_for_activated_sponsorships()
        partner_communications = self.env['partner.communication.job'].search([
            ('partner_id', '=', self.thomas.id),
            ('config_id', '=', welcome_active.id),
            ('state', '=', 'done')
        ])
        self.assertTrue(partner_communications)
        self.assertTrue(sponsorship.welcome_active_letter_sent)

    @mock.patch(mock_update_hold)
    @mock.patch(mock_get_pdf)
    @mock.patch(mock_get_infos)
    def test_no_welcome_letters(self, get_pdf, update_hold, get_infos):
        """
        Create a sponsorship, mark welcome letters already sent and test
        they are not sent when contract is validated and activated.
        """
        update_hold.return_value = True
        if self.is_travis:
            travis_path = 'addons/' + self.base_path
            with file_open(travis_path, 'rb') as test:
                get_pdf.return_value = test.read()
        else:
            cwd = os.getcwd()
            f_path = cwd + '/compassion-switzerland/' + self.base_path
            with open(f_path, 'rb') as fopen:
                get_pdf.return_value = fopen.read().decode('latin-1')

        # Creation of the sponsorship contract
        child = self.create_child(self.ref(11))
        sponsorship = self.create_contract(
            {
                'partner_id': self.thomas.id,
                'group_id': self.bvr_group.id,
                'child_id': child.id,
                'welcome_active_letter_sent': True
            },
            [{'amount': 50.0}]
        )

        # get_infos.return_value = {
        #     "BeneficiaryResponseList": [
        #             {"AcademicPerformance_Name": None,
        #              "AgeInYearsAndMonths": "10 Years",
        #              "BeneficiaryStatus": "Active",
        #              "BirthDate": "2010-01-01 00:00:00",
        #              "Beneficiary_CompassID": None,
        #              "CorrespondenceLanguage": "Swahili",
        #              "FirstName": "Test",
        #              "FullBodyImageURL": "",
        #              "FullName": "Last Test",
        #              "FundType": "Sponsorship",
        #              "Gender": "Male",
        #              "Beneficiary_GlobalID": "'wtfhurcpj'",
        #              "IsInHIVAffectedArea": True,
        #              "IsBirthDateEstimated": False,
        #              "IsOrphan": False,
        #              "IsSpecialNeeds": False,
        #              "LastName": "Last",
        #              "LastPhotoDate": "2019-04-29 00:00:00",
        #              "LastReviewDate": "2019-05-07 00:00:00",
        #              "Beneficiary_LocalID": "'iymppypvbiu'",
        #              "Beneficiary_LocalNumber": "10014",
        #              "PreferredName": "Ismail",
        #              "PrimaryCaregiverName": "Zainab Adam",
        #              "ProgramDeliveryType": "Home Based",
        #              "ChristianActivity_Name": ["Camp"],
        #              "ChronicIllness_Name": [],
        #              "Cluster_Name": "Tabora",
        #              "CognitiveAgeGroup_Name": "0-2",
        #              "Community_Name": "Isevya-TZ507",
        #              "Country": "Tanzania",
        #              "FieldOffice_Name": "Tanzania",
        #              "GradeLevelLocal_Name": "Not Enrolled",
        #              "GradeLevelUS_Name": "Not Enrolled",
        #              "HouseholdDuty_Name": ["No Household Duties - Too Young"],
        #              "ICP_Country": "Tanzania",
        #              "ICP_ID": "TZ0507",
        #              "ICP_Name": "Baptist Isevya",
        #              "PhysicalDisability_Name": [],
        #              "RecordType_Name": "Sponsorship Beneficiary",
        #              "FavoriteProjectActivity": ["Dancing and / or Drama"],
        #              "FavoriteSchoolSubject": ["Music"],
        #              "FormalEducationLevel": None,
        #              "MajorOrCourseOfStudy": None,
        #              "NotEnrolledInEducationReason": "Under Age",
        #              "PlannedCompletionDate": "2040-04-16 00:00:00",
        #              "PlannedCompletionDateChangeReason": None,
        #              "ReviewStatus": "Approved",
        #              "SponsorshipStatus": None,
        #              "ThingsILike": ["Dancing", "Dolls"],
        #              "VocationalTrainingType_Name": "Not enrolled",
        #              "HangulName": "\uc774\uc2a4 \ub9c8\uc77c \uc774\ube0c\ub77c\ud798 \ub77c\uc790\ube0c\ ",
        #              "HangulPreferredName": "\uc774\uc2a4 \ub9c8\uc77c\ ",
        #              "SourceKitName": "BeneficiaryKit",
        #              "BeneficiaryHouseholdList": [
        #                  {"FemaleGuardianEmploymentStatus": "Sometimes Employed",
        #                   "FemaleGuardianOccupation": "Other",
        #                   "Household_ID": "H-02887386",
        #                   "IsNaturalFatherLivingWithChild": False,
        #                   "IsNaturalMotherLivingWithChild": True,
        #                   "MaleGuardianEmploymentStatus": None,
        #                   "MaleGuardianOccupation": None,
        #                   "Household_Name": "Rajab Family (Ismail)",
        #                   "NaturalFatherAlive": "Yes",
        #                   "NaturalMotherAlive": "Yes",
        #                   "NumberOfBrothers": 1,
        #                   "NumberOfSiblingBeneficiaries": 1,
        #                   "NumberOfSisters": 0,
        #                   "ParentsMaritalStatus": "Never Married",
        #                   "ParentsTogether": "No",
        #                   "YouthHeadedHousehold": False,
        #                   "RevisedValues": "RevisedValuesToUpdate",
        #                   "SourceKitName": "HouseholdKit",
        #                   "BeneficiaryHouseholdMemberList": [
        #                       {"FullName": None,
        #                        "GlobalID": None,
        #                        "LocalID": None,
        #                        "HouseholdMemberRole": "Mother",
        #                        "IsCaregiver": True,
        #                        "IsPrimaryCaregiver": True,
        #                        "HouseholdMember_Name": "Zainab Adam"},
        #                       {"FullName": "Ismail Ibrahim Rajab",
        #                        "GlobalID": "08090897",
        #                        "LocalID": "TZ050710014",
        #                        "HouseholdMemberRole": "Beneficiary - Male",
        #                        "IsCaregiver": False,
        #                        "IsPrimaryCaregiver": False,
        #                        "HouseholdMember_Name": "Ismail Ibrahim Rajab"}]}]}]}

        self.validate_sponsorship(sponsorship)
        self.assertEqual(sponsorship.sds_state, 'active')
        # Perform action rules (shouldn't do anything)
        eleven_days_ago = date.today() - relativedelta(days=11)
        sponsorship.sds_state_date = fields.Date.to_string(eleven_days_ago)
        self.env['base.automation']._check()
        self.assertEqual(sponsorship.sds_state, 'active')
        welcome_email = self.env.ref(
            'partner_communication_switzerland.planned_welcome')
        partner_communications = self.env['partner.communication.job'].search([
            ('partner_id', '=', self.thomas.id),
            ('config_id', '=', welcome_email.id)
        ])
        self.assertFalse(partner_communications)

        # Now test the welcome active communication
        sponsorship.force_activation()
        two_days_ago = date.today() - relativedelta(days=2)
        sponsorship.activation_date = fields.Date.to_string(two_days_ago)
        sponsorship.start_date = fields.Date.to_string(eleven_days_ago)
        sponsorship._send_welcome_active_letters_for_activated_sponsorships()
        welcome_active = self.env.ref(
            'partner_communication_switzerland.welcome_activation')
        partner_communications = self.env['partner.communication.job'].search([
            ('partner_id', '=', self.thomas.id),
            ('config_id', '=', welcome_active.id)
        ])
        self.assertFalse(partner_communications)

    @mock.patch(mock_update_hold)
    @mock.patch(mock_get_pdf)
    def test_no_welcome_letter_for_transfers(self, get_pdf, update_hold):
        child = self.create_child(self.ref(11))
        transfer_origin = self.env['recurring.contract.origin'].create({
            'type': 'transfer'
        })
        sponsorship = self.create_contract(
            {
                'partner_id': self.michel.id,
                'child_id': child.id,
                'group_id': self.lsv_group.id,
                'origin_id': transfer_origin.id

            },
            [{'amount': 50.0}]
        )
        partner_communications = self.env['partner.communication.job']
        count_before = partner_communications.search_count([])

        sponsorship.send_welcome_letter()

        self.assertEqual(sponsorship.sds_state, 'active')
        # No new communication is generated
        self.assertEqual(count_before, partner_communications.search_count([]))
