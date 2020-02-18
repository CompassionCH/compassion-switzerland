##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from dateutil.relativedelta import relativedelta

from odoo import models, api, fields


class PostponeWaitingReminderWizard(models.TransientModel):
    _name = 'postpone.waiting.reminder.wizard'

    sponsorship_id = fields.Many2one(
        'recurring.contract', string='Sponsorship', required=True,
    )
    next_reminder = fields.Datetime(required=True)
    next_reminder_type = fields.Selection([
        ('0', 'Reminder 1'),
        ('1', 'Reminder 2'),
        ('2', 'Reminder 3'),
    ], required=True)
    hold_id = fields.Many2one(
        'compassion.hold', related='sponsorship_id.child_id.hold_id'
    )

    @api.model
    def _select_reminder_type(self):
        return

    @api.multi
    def postpone_reminder(self):
        self.ensure_one()
        # Cancel existing reminders
        self.env['partner.communication.job'].search([
            ('partner_id', '=', self.sponsorship_id.partner_id.id),
            ('config_id.name', 'ilike', 'Waiting reminder'),
            ('state', '!=', 'done')
        ]).unlink()

        # Set expiration of hold
        hold_expiration = fields.Datetime.from_string(
            self.next_reminder) + relativedelta(days=7)
        self.hold_id.write({
            'expiration_date': fields.Datetime.to_string(hold_expiration),
            'no_money_extension': int(self.next_reminder_type)
        })
        return True
