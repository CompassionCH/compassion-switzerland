import logging
from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)


@openupgrade.migrate()
def migrate(env, installed_version):
    if not installed_version:
        return

    def get_partners_to_change():
        all_companies_refs = env["res.partner"].search([("is_company", "=", True)]).mapped("ref")
        return env["res.partner"].search([("is_company", "=", False), ("ref", "in", all_companies_refs)])

    partner_to_change = get_partners_to_change()
    sponsor_to_change = partner_to_change.filtered(lambda p: any(p.mapped("sponsorship_ids.is_active")))

    for partner in partner_to_change - sponsor_to_change:
        partner.ref = env["ir.sequence"].next_by_code("partner.ref")

    companies_to_changes = sponsor_to_change.mapped("parent_id")
    companies_w_no_sponsors = companies_to_changes.filtered(lambda p: not all(p.mapped("sponsorship_ids.is_active")))

    for company in companies_w_no_sponsors:
        company.ref = env["ir.sequence"].next_by_code("partner.ref")

    manuel_update_required = get_partners_to_change()
    if manuel_update_required:

        output = "Reference update could not automatically be done for the following instances :"
        output += "\n".join(manuel_update_required.mapped("ref"))

        logging.warning(output)

        with open("ref duplication issue.txt", "w") as f:
            f.write(output)
