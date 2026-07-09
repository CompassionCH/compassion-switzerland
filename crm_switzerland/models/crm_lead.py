from odoo import api, fields, models


class Lead(models.Model):
    _inherit = "crm.lead"

    # Remove the compute attribute from the email_from field
    email_from = fields.Char(compute=False, inverse=False)

    # Keep possibility to sync email_from with partner email from the UI.
    @api.onchange("partner_id")
    def onchange_partner_id(self):
        if self.partner_id.email:
            self.email_from = self.partner_id.email

    def _sync_church_salesperson(self):
        if self.env.context.get("skip_church_salesperson_sync"):
            return
        for lead in self:
            church = lead.partner_id
            if not church.is_church or not lead.user_id:
                continue
            church.with_delay_sh(
                "sync_salesperson_from_lead",
                lead.user_id.id,
                lead.id,
                identity_key=(
                    f"res.partner.sync_salesperson_from_lead.{church.id}.{lead.id}"
                ),
            )

    @api.model_create_multi
    def create(self, vals_list):
        leads = super().create(vals_list)
        leads._sync_church_salesperson()
        return leads

    def write(self, vals):
        res = super().write(vals)
        if "user_id" in vals:
            self._sync_church_salesperson()
        return res
