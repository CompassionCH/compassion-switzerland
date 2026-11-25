from odoo import fields, models


class MailActivity(models.Model):
    _inherit = "mail.activity"

    # Portal users cannot work on activities
    user_id = fields.Many2one(domain=[("share", "=", False)])


class MailActivitySchedule(models.TransientModel):
    _inherit = "mail.activity.schedule"

    activity_user_id = fields.Many2one(domain=[("share", "=", False)])
