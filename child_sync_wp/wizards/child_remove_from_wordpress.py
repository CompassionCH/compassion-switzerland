##############################################################################
#
#    Copyright (C) 2014-2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: David Coninckx <david@coninckx.com>, Emanuel Cino
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import fields, models
from odoo.exceptions import UserError
from odoo.tools.translate import _


class ChildRemoveFromWordpress(models.TransientModel):
    _name = "child.remove.from.wordpress.wizard"
    _description = "Remove children from WordPress"

    child_ids = fields.Many2many(
        "compassion.child",
        compute="_compute_active_ids",
        string="Selected children",
        default=lambda c: c._compute_active_ids(),
    )

    def _compute_active_ids(self):
        self.child_ids = None
        children = self.env["compassion.child"].browse(
            self.env.context.get("active_ids")
        )
        valid_children = children.filtered(lambda c: c.state == "I")
        for wizard in self:
            wizard.child_ids = valid_children
        return valid_children

    def remove_child_from_internet(self):
        children = self.child_ids
        if not children:
            raise UserError(
                _("None of the selected children are currently on the website.")
            )
        children.remove_from_wordpress()
        still_online = children.filtered(lambda c: c.state == "I")
        if still_online:
            raise UserError(_("The website could not remove the selected children."))
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Wordpress"),
                "message": _("%s children removed from the website.") % len(children),
                "type": "success",
                "next": {"type": "ir.actions.act_window_close"},
            },
        }
