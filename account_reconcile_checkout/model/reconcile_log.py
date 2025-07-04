from odoo import models, fields

class PostfinanceReconcileLog(models.Model):
    _name = 'postfinance.reconcile.log'
    _description = 'PostFinance Reconciliation Log'
    _order = 'create_date desc'

    message = fields.Text(string="Message", required=True)
    log_type = fields.Selection([
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('info', 'Info'),
    ], string="Type", required=True)
    create_date = fields.Datetime(string="Date", readonly=True)