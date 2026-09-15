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


def _child_refs(children, limit=10):
    refs = [child.local_id or f"#{child.id}" for child in children]
    if len(refs) > limit:
        return ", ".join(refs[:limit]) + _(" and %s more") % (len(refs) - limit)
    return ", ".join(refs)


class ChildOnWorpressWizard(models.TransientModel):
    _name = "child.on.wordpress.wizard"
    _description = "Put children on WordPress"

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
        # add_to_wordpress only ever uploads consigned children
        valid_children = children.filtered(lambda c: c.state == "N")
        for wizard in self:
            wizard.child_ids = valid_children
        return valid_children

    def put_child_on_internet(self):
        children = self.child_ids
        if not children:
            raise UserError(
                _("None of the selected children can be put on the website.")
            )
        children.add_to_wordpress()
        pushed = children.filtered(lambda c: c.state == "I")
        skipped = children - pushed
        if not pushed:
            raise UserError(
                _("No child could be put on the website: %s") % _child_refs(skipped)
            )
        message = _("%(pushed)s of %(total)s children put on the website.") % {
            "pushed": len(pushed),
            "total": len(children),
        }
        if skipped:
            # the notification body is escaped html: a newline would collapse
            message += " " + _(
                "Skipped (missing description or photo, or completing "
                "within 2 years): %s"
            ) % _child_refs(skipped)
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Wordpress"),
                "message": message,
                "type": "warning" if skipped else "success",
                "sticky": bool(skipped),
                "next": {"type": "ir.actions.act_window_close"},
            },
        }
