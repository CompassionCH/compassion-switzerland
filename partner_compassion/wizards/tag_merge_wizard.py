##############################################################################
#
#    Copyright (C) 2020 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Sylvain Losey <sylvainlosey@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import fields, models, _
from odoo.exceptions import UserError


class TagMergeWizard(models.TransientModel):
    """
    Merge 2 or more tags into a single one.
    """

    _name = "res.partner.category.merge"
    _description = "Tag Merge Wizard"

    dest_tag_id = fields.Many2one(
        "res.partner.category",
        "Destination tag",
        default=lambda s: s._default_dest(),
        required=True,
    )
    tag_ids = fields.Many2many(
        "res.partner.category", string="Tags", default=lambda s: s._default_tags()
    )

    def _default_tags(self):
        return self.env.context.get("active_ids")

    def _default_dest(self):
        return (
            self.env.context.get("active_id")
            or self.env.context.get("active_ids", [0])[0]
        )

    def action_merge(self):
        self.ensure_one()
        if len(self.tag_ids) < 2:
            raise UserError(_("Please select at least 2 tags."))

        merged_partners = self.tag_ids.mapped("partner_ids")
        tags_to_remove = self.tag_ids - self.dest_tag_id
        tags_to_remove.unlink()
        merged_partners.write({"category_id": [(4, self.dest_tag_id.id)]})
        return True
