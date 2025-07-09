from odoo import fields, models


class GoogleAnalyticsDataLine(models.Model):
    _name = "google.analytics.data.line"
    _description = "Google Analytics Data Line"

    report_id = fields.Many2one("google.analytics.data", string="Report")
    url = fields.Char("URL")
    device = fields.Char("Device")
    page_views_total = fields.Integer("Page Views - Total")
    active_users_total = fields.Integer("Active Users - Total")
