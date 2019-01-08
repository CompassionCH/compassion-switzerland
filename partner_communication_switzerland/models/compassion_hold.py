# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from datetime import datetime

from odoo import api, models, fields

from odoo.addons.child_compassion.models.compassion_hold import HoldType


class CompassionHold(models.Model):
    """ Send Communication when Hold Removal is received. """
    _inherit = 'compassion.hold'

    no_money_extension_duration = fields.Integer(
        compute='_compute_no_money_extension_duration')

    @api.multi
    def _compute_no_money_extension_duration(self):
        """
        Gets the default No Money hold extension duration
        :return: integer: hold duration in days
        """
        settings = self.env['availability.management.settings']
        for hold in self:
            if hold.no_money_extension < 2:
                hold.no_money_extension_duration = settings.get_param(
                    'no_money_hold_duration')
            else:
                hold.no_money_extension_duration = settings.get_param(
                    'no_money_hold_extension')

    @api.model
    def beneficiary_hold_removal(self, commkit_data):
        ids = super(CompassionHold, self).beneficiary_hold_removal(
            commkit_data)
        job_obj = self.env['partner.communication.job']
        now = datetime.now()
        for hold in self.browse(ids).filtered(
                lambda h: h.channel in ('ambassador', 'event') and
                fields.Datetime.from_string(h.expiration_date) > now):
            communication_type = self.env.ref(
                'partner_communication_switzerland.hold_removal')
            job_obj.create({
                'config_id': communication_type.id,
                'partner_id': hold.primary_owner.partner_id.id,
                'object_ids': hold.id,
                'user_id': communication_type.user_id.id,
                'auto_send': True,
            })
            if hold.ambassador:
                job_obj.create({
                    'config_id': communication_type.id,
                    'partner_id': hold.ambassador.id,
                    'object_ids': hold.id,
                    'user_id': communication_type.user_id.id,
                })

        return ids

    @api.multi
    def postpone_no_money_hold(self, additional_text=None):
        """
        Send a communication to sponsor for reminding the payment.
        TODO: Attach a payment slip
        :param additional_text: text to add in the notification to hold owner
        :return: None
        """
        failed = self.env[self._name]
        # Last reminder: cancellation notice
        communication_type = self.env.ref(
            'partner_communication_switzerland.'
            'sponsorship_waiting_reminder_3')
        failed += self.filtered(
            lambda h: h.no_money_extension > 1)._send_hold_reminder(
            communication_type)

        # Second reminder
        communication_type = self.env.ref(
            'partner_communication_switzerland.'
            'sponsorship_waiting_reminder_2')
        failed += self.filtered(
            lambda h: h.no_money_extension == 1)._send_hold_reminder(
            communication_type)

        # First reminder
        communication_type = self.env.ref(
            'partner_communication_switzerland.'
            'sponsorship_waiting_reminder_1')
        failed += self.filtered(
            lambda h: h.no_money_extension == 0)._send_hold_reminder(
            communication_type)

        if failed:
            # Send warning to Admin users
            child_codes = failed.mapped('child_id').read(['local_id'])
            base_url = self.env['ir.config_parameter'].get_param(
                'web.base.url')
            links = [
                '<a href="{}/web#id={}&view_type=form&model=compassion.child'
                '&menu_id=442&action=581">{}</a>'.format(
                    base_url, data['id'], data['local_id'])
                for data in child_codes
            ]
            hold_string = list()
            for i in range(0, len(failed)):
                hold_string.append(failed[i].hold_id + ' (' + links[i] + ' )')
            self.env['mail.mail'].create({
                'subject': 'URGENT: Postpone no money holds failed!',
                'author_id': self.env.user.partner_id.id,
                'recipient_ids': [(6, 0, [18000, 13])],
                'body_html': 'These holds should be urgently verified: <br/>'
                '<br/>' + ', '.join(hold_string)
            }).send()

    def _send_hold_reminder(self, communication):
        """
        Sends the hold reminder communication to sponsors and postpone the
        hold.
        :param communication: the type of communication
        :return: recordset of failed updated holds.
        """
        notification_text = "\n\nA reminder has been prepared for the " \
            "sponsor {} ({})"
        failed = self.env[self._name]
        for hold in self.filtered(
                lambda h: h.child_id.sponsorship_ids and
                h.type in (HoldType.NO_MONEY_HOLD.value,
                           HoldType.SUB_CHILD_HOLD.value)).with_context(
                default_auto_send=False, default_print_subject=False,
                default_print_header=True):
            sponsorship = hold.child_id.sponsorship_ids[0]
            sponsor = hold.child_id.sponsor_id
            # Filter draft sponsorships and where we wait for
            # the bank authorization
            if sponsorship.state == 'draft' or \
                    (sponsorship.state == 'mandate' and sponsor.bank_ids):
                try:
                    super(CompassionHold, hold).postpone_no_money_hold()
                    hold.no_money_extension -= 1
                    continue
                except:
                    failed += hold
                    continue
            # Cancel old invoices
            if len(sponsorship.due_invoice_ids) > 1:
                for invoice in sponsorship.due_invoice_ids[:-1]:
                    invoice.action_invoice_cancel()
            try:
                super(CompassionHold, hold).postpone_no_money_hold(
                    notification_text.format(sponsor.name, sponsor.ref))
                sponsorship.send_communication(communication,
                                               correspondent=False)
            except:
                failed += hold
        return failed
