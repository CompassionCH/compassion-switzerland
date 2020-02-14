##############################################################################
#
#    Copyright (C) 2017 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Marco Monzione <marco.mon@windowslive.com>, Emanuel Cino
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models, fields
from odoo.addons.child_compassion.models.compassion_hold import HoldType
from dateutil import relativedelta
from datetime import date


class MonitorCorrectErrors(models.Model):
    _name = 'monitor.correct.errors'
    _description = "Monitor for errors"

    error_ids = fields.One2many('error.log', 'monitor_id')

    def process_errors(self):

        current_run = self.create({})
        # Commit the new run
        self.env.cr.commit()  # pylint: disable=invalid-commit
        current_run._fix_sponsorship()
        current_run._fix_hold()
        current_run._fix_sbc()

        current_run._send_mail()

    def _fix_hold(self):
        '''
        This method fixe problem with children that have no hold, or the hold
        is in the wrong type.
        :return: -
        '''

        # Retrieve all child where the sponsorship is in state waiting or
        # mandate and the child hold type is different from no_money_hold.
        list_of_child_other_hold = self.env['recurring.contract'].search([
            ('state', 'in', ['waiting', 'mandate']),
            ('type', '=', 'S'),
            ('child_id.hold_id.type', '!=', HoldType.NO_MONEY_HOLD.value)]).\
            mapped('child_id')

        # Retrieve all child where the sponsorship is in state waiting or
        # mandate and the child has no hold.
        list_of_child_without_hold = self.env['recurring.contract'].search([
            ('state', 'in', ['waiting', 'mandate']),
            ('type', '=', 'S'),
            ('child_id.hold_id', '=', False)]).mapped('child_id')

        error_log = {'error_type': 'Invalid no money holds'}

        # Set the hold type to "no money hold".
        for child in list_of_child_other_hold:
            try:
                error_log.update({
                    'record': 'invalid hold type',
                    'record_id': child.id,
                    'record_name': 'child local id : ' + str(child.local_id),
                    'record_model': 'compassion.child'
                })

                child.hold_id.type = HoldType.NO_MONEY_HOLD.value
                # Commit when the hold is changed
                self.env.cr.commit()  # pylint: disable=invalid-commit
                error_log.update({
                    'action': 'hold type corrected',
                    'action_model': 'compassion.hold',
                    'action_name': 'hold',
                    'action_id': child.hold_id.id
                })

            except:
                self.env.clear()
                self._create_reservation(child, error_log)
            self.error_ids += self.env['error.log'].create(error_log)
            # Commit when a error_log is created
            self.env.cr.commit()  # pylint: disable=invalid-commit

        # Create new hold for child without hold.
        for child in list_of_child_without_hold:
            error_log.update({
                'record': 'missing hold',
                'record_id': child.id,
                'record_name': "child local id : " + str(child.local_id),
                'record_model': 'compassion.child'
            })

            self._create_new_hold(child, error_log)

            self.error_ids += self.env['error.log'].create(error_log)
            # Commit when a error_log is created
            self.env.cr.commit()  # pylint: disable=invalid-commit

    def _fix_sbc(self):
        '''
        This method send a warning for letters that are not been delivred to
        the sponsor, or letters that has been in the queue for too long.
        :return: -
        '''

        limit_date = date.today() - relativedelta(days=30)
        list_error_correspondence = self.env['correspondence'].search([
            ('state', '=', 'Published to Global Partner'),
            ('sent_date', '=', False),
            ('letter_delivered', '=', False),
            ('status_date', '<', fields.Date.to_string(limit_date))
        ])

        error_log = {'error_type': 'B2S letters not sent'}

        for correspondence in list_error_correspondence:
            error_log.update({
                'record': 'Letters not send',
                'record_id': correspondence.id,
                'record_name': correspondence.name,
                'record_model': 'correspondence'
            })
            self.error_ids += self.env['error.log'].create(error_log)

        list_correspondence_translation_queue_error = \
            self.env['correspondence'].search([
                ('state', '=', 'Global Partner translation queue'),
                ('status_date', '<', fields.Date.to_string(limit_date))
            ])

        error_log['error_type'] = "Letters in translation queue for too long"
        for correspondence in list_correspondence_translation_queue_error:
            error_log.update({
                'record': 'Letters in queue for too long',
                'record_id': correspondence.id,
                'record_name': correspondence.name,
                'record_model': 'correspondence'
            })

            self.error_ids += self.env['error.log'].create(error_log)

        list_correspondence_scan_error = self.env['correspondence'].\
            search([('state', '=', 'Received in the system'),
                    ('status_date', '<', fields.Date.to_string(limit_date))])

        error_log['error_type'] = "Letters scanned in for too long"

        for correspondence in list_correspondence_scan_error:
            error_log.update({
                'record': 'Letters scanned in for too long',
                'record_id': correspondence.id,
                'record_name': correspondence.name,
                'record_model': 'correspondence'
            })

            self.error_ids += self.env['error.log'].create(error_log)

    def _fix_sponsorship(self):
        '''
        This method fix the sponsorships that are not in the correct state, or
        sponsorship where the child has no link to the sponsor.
        :return:
        '''

        # Search for child with a sponsor but not in the correct state
        child_wrong_state = self.env['recurring.contract'].search([
            ('state', '=', 'active'),
            ('type', '=', 'S'),
            ('child_id.sponsor_id', '!=', False),
            ('child_id.state', '!=', 'P')
        ]).mapped('child_id')

        error_log = {'error_type': 'Sponsored child not in correct state'}

        for child in child_wrong_state:
            error_sponsorship = self.env['recurring.contract'].search(
                [('child_id', '=', child.id),
                 ('state', 'not in', ['terminated', 'cancelled'])])
            error_log.update({
                'record': 'child not in sponsored state',
                'record_id': error_sponsorship.id,
                'record_name': error_sponsorship.name,
                'record_model': 'recurring.contract'
            })

            try:
                child.write({'hold_id': 2})
                child.create_workflow()
                child.hold_id = False
                error_log['action'] = "workflow reset"
            except:
                error_log['action'] = "The reset of the workflow failed"

            error_log.update({
                'action_model': 'compassion.child',
                'action_id': child.id,
                'action_name': 'child local id : ' + str(child.local_id),
            })
            self.error_ids += self.env['error.log'].create(error_log)

        # Search for child with active sponsorship and no sponsor
        child_without_sponsor = self.env['recurring.contract'].search([
            ('state', '=', 'active'),
            ('type', '=', 'S'),
            ('child_id.sponsor_id', '=', False),
            ('child_id.state', '=', 'P')
        ]).mapped('child_id')

        error_log = {'error_type': 'Sponsored child has no sponsor'}

        for child in child_without_sponsor:
            # Search for the sponsorhip who belong the child
            error_sponsorship = self.env['recurring.contract'].search([
                ('child_id', '=', child.id),
                ('state', 'not in', ['terminated', 'cancelled'])
            ])

            error_log.update({
                'record': 'child not linked',
                'record_id': error_sponsorship.id,
                'record_name': error_sponsorship.name,
                'record_model': 'recurring.contract'
            })

            child.sponsor_id = error_sponsorship.correspondent_id

            error_log.update({
                'action': 'ink created',
                'action_model': 'compassion.child',
                'action_name': 'child local id : ' + str(child.local_id),
                'action_id': child.id
            })

            self.error_ids += self.env['error.log'].create(error_log)

    def _create_new_hold(self, child, error_log):
        '''
        Try to create a new hold (no money hold) for the given child.
        :param child: The child to link to the hold
        :return: -
        '''

        # Create the new hold
        hold = self.env['compassion.hold'].create({
            'expiration_date': self.env['compassion.hold'].
            get_default_hold_expiration(HoldType.NO_MONEY_HOLD),
            'child_id': child.id,
            'type': HoldType.NO_MONEY_HOLD.value
        })

        try:
            # Confirm within the global server if the child is available.
            hold.update_hold()
            child.hold_id = hold
            # Commit when a hold is placed
            self.env.cr.commit()  # pylint: disable=invalid-commit
            error_log.update({
                'action': 'new hold create',
                'action_model': 'compassion.hold',
                'action_id': hold.id,
                'action_name': 'hold'
            })

        except Exception:

            # Create a reservation if hold has not been placed.
            self.env.clear()
            self._create_reservation(child, error_log)

    def _create_reservation(self, child, error_log):
        '''
        Create a new reservation.
        :param child: the child to reserve
        :return: -
        '''

        # Check if there is already a reservation for that child.
        previous_reservation = self.env['compassion.reservation'].search([
            ('child_global_id', '=', child.global_id),
            ('state', '!=', 'expired')])

        # If not, we create a new reservation
        if not previous_reservation:
            reservation = self.env['compassion.reservation'].create({
                'child_id': child.id,
                'reservation_type': 'child',
                'reservation_expiration_date': self.env[
                    'compassion.hold'].get_default_hold_expiration(
                    HoldType.CONSIGNMENT_HOLD),
                'expiration_date': self.env[
                    'compassion.hold'].get_default_hold_expiration(
                    HoldType.CONSIGNMENT_HOLD),
                'comments': "Automatic reservation place for missing hold"
            })
            # Commit when we create a reservation to avoid its deletion
            self.env.cr.commit()   # pylint: disable=invalid-commit
            # Activation of the reservation
            reservation.handle_reservation()
            error_log.update({
                'action': 'new reservation created',
                'action_model': 'compassion.reservation',
                'action_id': reservation.id,
                'action_name': 'reservation'
            })

        else:
            error_log.update({
                'action': 'reservation already exist',
                'action_model': 'compassion.reservation',
                'action_id': previous_reservation.id,
                'action_name': 'reservation'
            })

    def _send_mail(self):

        message_body = ""

        for error_type in self.env['error.log'].get_error_type():
            # Get the error type from the list.
            message_body += "<h4>" + error_type + "</h4>"
            message_body += "<table class=\"editorDemoTable\" border=\"1\">"
            message_body += "<tr>"
            message_body += "<td><h4>" + "Record" + "</h4></td>"
            message_body += "<td><h4>" + "Error type" + "</h4></td>"
            message_body += "<td><h4>" + "Action" + "</h4></td>"

            for error in self.error_ids.filtered(
                    lambda e: e.error_type == error_type):
                message_body += "<tr>"
                message_body += "<td>" + error.format_record_url() + "</td>"
                message_body += "<td>" + error.record + "</td>"
                if error.action:
                    message_body += "<td>" + error.action + " " + \
                                    error.format_action_url() + "</td>"
                else:
                    message_body += "<td> - </td>"
                message_body += "</tr>"

            message_body += "</tr>"
            message_body += "</table>"

        mail = self.env['mail.mail'].create({
            'email_to': "ecino@compassion.ch",
            'subject': "Odoo Weekly Monitoring Report",
            'body_html': message_body
        })
        mail.send()
