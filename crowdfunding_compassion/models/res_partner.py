from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    crowdfunding_project_count = fields.Integer(
        compute='_compute_crowdfunding_project_count', string='Crowdfunding')

    def _compute_crowdfunding_project_count(self):
        for record in self:
            record.crowdfunding_project_count = self.env[
                'crowdfunding.participant'].search_count(
                [('partner_id', '=', record.id)])

    def open_crowdfunding_project(self):
        project_ids = self.env['crowdfunding.participant'].search(
            [('partner_id', '=', self.id)]).mapped('project_id')
        return {
            "name": "Crowdfunding Project",
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "tree,form",
            "res_model": "crowdfunding.project",
            "domain": [("id", "in", project_ids.ids)],
            "target": "current",
        }
