##############################################################################
#
#    Copyright (C) 2020 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Sylvain Losey <sylvainlosey@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class TagMergeWizard(models.TransientModel):
    """
    Merge 2 or more tags into a single one.
    """
    _name = "res.partner.category.merge"
    _description = "Tag Merge Wizard"

    new_name = fields.Char(required=True)
    tag_ids = fields.Many2many("res.partner.category", string="Tags")

    @api.multi
    def action_merge(self):
        self.ensure_one()
        if len(self.tag_ids) < 2:
            raise UserError(_("Please select at least 2 tags."))

        merged_partners = [tag.partner_ids for tag in self.tag_ids]
        merged_partners_ids = [partner.id for x in merged_partners for partner in x]

        # Create a tag with the new name and all unique partner_ids of the merged ones
        self.env["res.partner.category"].create({
            "name": self.new_name,
            "partner_ids": [(6, 0, list(set(merged_partners_ids)))]
        })

        # Delete the merged tags
        self.tag_ids.unlink()

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        # Populate wizard tag ids from selected tags stored in context
        res.update({'tag_ids': self.env.context.get('active_ids', [])})
        return res
