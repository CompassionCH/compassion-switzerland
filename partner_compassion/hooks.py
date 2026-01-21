def post_init_hook(env):
    sponsor_cat = env.ref("partner_compassion.res_partner_category_sponsor")
    for partner in env["res.partner"].search([("number_sponsorships", ">", 0)]):
        partner.category_id += sponsor_cat
