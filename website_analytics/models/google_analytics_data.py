import pandas as pd
import base64
import logging
from odoo import models, fields, api
from odoo.exceptions import UserError
from google.oauth2 import service_account
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import DateRange, Metric, Dimension, RunReportRequest
import matplotlib.pyplot as plt

_logger = logging.getLogger(__name__)


class GoogleAnalyticsData(models.Model):
    _name = 'google.analytics.data'
    _description = 'Google Analytics Data'

    name = fields.Char(string="Report Name")
    language = fields.Selection([
        ('all', 'All'), ('fr', 'French'), ('de', 'German'), ('it', 'Italian')],
        string="Language", default='all')
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    device_category = fields.Selection([
        ('all', 'All Devices'),
        ('mobile', 'Mobile'),
        ('tablet', 'Tablet'),
        ('desktop', 'Desktop')],
        string="Device Category", default='all')
    report_lines = fields.One2many('google.analytics.data.line', 'report_id', string="Report Lines")

    # How to retrieve data from the Google Analytics API
    def fetch_data(self):
        try:
            start_date = self.start_date.strftime('%Y-%m-%d')
            end_date = self.end_date.strftime('%Y-%m-%d')

            KEY_FILE_LOCATION = '/home/kyraaz/odoo-compassion/odoo/odoo/local-addons/compassion-switzerland/website_analytics/models/website analytics data API-0d9158d758ea.json'
            SCOPES = ['https://www.googleapis.com/auth/analytics.readonly']
            credentials = service_account.Credentials.from_service_account_file(KEY_FILE_LOCATION, scopes=SCOPES)
            client = BetaAnalyticsDataClient(credentials=credentials)

            request = RunReportRequest(
                property='properties/251860109',
                date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
                metrics=[Metric(name="screenPageViews"), Metric(name="activeUsers")],
                dimensions=[Dimension(name="pagePath"), Dimension(name="deviceCategory")]
            )
            response = client.run_report(request)

            if not response.rows:
                raise UserError("No data found for the selected period.")

            rows = []
            for row in response.rows:
                rows.append({
                    'URL': row.dimension_values[0].value,
                    'Device': row.dimension_values[1].value,
                    'Page views - total': int(row.metric_values[0].value),
                    'Active users - total': int(row.metric_values[1].value)
                })

            df = pd.DataFrame(rows)

            # Data filtering according to selected criteria (devices and languages)
            if self.device_category and self.device_category != 'all':
                df = df[df['Device'] == self.device_category]

            if self.language and self.language != 'all':
                if self.language == 'fr':
                    df = df[~df['URL'].str.contains('/de/') & ~df['URL'].str.contains('/it/')]
                elif self.language == 'de':
                    df = df[df['URL'].str.contains('/de/')]
                elif self.language == 'it':
                    df = df[df['URL'].str.contains('/it/')]

            df = df[df['Page views - total'] >= 5]

            return df

        except Exception as e:
            raise UserError(f"Error fetching data: {e}")

    # Creation of new lines in the ‘google.analytics.data.line’ template
    def generate_report(self):
        if not self.start_date or not self.end_date:
            raise UserError("Start Date and End Date are required.")

        try:
            df = self.fetch_data()
            if df.empty:
                raise UserError("The DataFrame is empty, no data to display.")

            self.report_lines.unlink()

            for _, row in df.iterrows():
                _logger.info(f"Creating line for {row['URL']}")
                self.env['google.analytics.data.line'].create({
                    'report_id': self.id,
                    'url': row['URL'],
                    'device': row['Device'],
                    'page_views_total': row['Page views - total'],
                    'active_users_total': row['Active users - total'],
                })
        except Exception as e:
            raise UserError(f"Error generating the report: {e}")

    @api.model
    def create(self, vals):
        record = super(GoogleAnalyticsData, self).create(vals)
        record.generate_report()
        return record

    def write(self, vals):
        res = super(GoogleAnalyticsData, self).write(vals)
        self.generate_report()
        return res

    def generate_report_button(self):
        return self.generate_report()
