import uuid
from odoo import api, SUPERUSER_ID


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    sponsor_cat = env.ref("partner_compassion.res_partner_category_sponsor")
    for partner in env["res.partner"].search([("active", "in", [True, False])]):
        partner.uuid = uuid.uuid4()
        if partner.has_sponsorships:
            partner.category_id += sponsor_cat
