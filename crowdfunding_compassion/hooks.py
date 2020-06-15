import logging
from odoo import api, SUPERUSER_ID
from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)

_xml_mapping = {
    "Project creation confirmation": [
        "config_project_confirmation", "project_join"
    ],
    "Project published": [
        "config_project_published", "project_published_email_template"
    ],
    "Project joined confirmation": [
        "config_project_join", ""
    ],
    "Donation successful": [
        "config_donation_successful_email_template",
        "donation_successful_email_template"
    ],
    "Donation notification": [
        "config_donation_received", "donation_received_email_template"
    ]
}


def pre_init_hook(cr):
    # Attach Prod mail templates to XML records
    env = api.Environment(cr, SUPERUSER_ID, {})
    comm_configs = env["partner.communication.config"].search([
        ("name", "ilike", "crowdfunding")])
    for prod_config in comm_configs:
        _logger.info("Adding XMLID for Crowdfunding communication %s", prod_config.name)
        xml_id = _xml_mapping.get(prod_config.name.replace("Crowdfunding - ", ""))
        if xml_id:
            openupgrade.add_xmlid(
                cr, "crowdfunding_compassion", xml_id[0],
                "partner.communication.job", prod_config.id
            )
            if prod_config.email_template_id:
                openupgrade.add_xmlid(
                    cr, "crowdfunding_compassion", xml_id[1],
                    "mail.template", prod_config.email_template_id.id
                )
