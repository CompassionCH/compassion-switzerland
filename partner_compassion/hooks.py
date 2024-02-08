from odoo import SUPERUSER_ID, api


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    sponsor_cat = env.ref("partner_compassion.res_partner_category_sponsor")
    for partner in env["res.partner"].search([("has_sponsorships", "=", True)]):
        partner.category_id += sponsor_cat
