import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)

# T3561: record rules still holding v14 fields. Odoo raises an error as soon as
# such a rule is evaluated, which blocks every user of its groups (ex: moving a
# task to another project fails for the translators, as reading the followers
# evaluates the rule on the partners).
# Some internal users were also left in the portal group by the migration: Odoo
# then handles them as portal users, who can only change a few fields of a task.

# Rules created by hand in the database (name, field of the broken domain)
FIXED_RULES = {
    # has_sponsorships was removed, it was set to number_sponsorships > 0
    ("Translator read sponsors", "has_sponsorships"): (
        "['|', ('number_sponsorships', '>', 0), ('id', '=', user.partner_id.id)]"
    ),
}
ARCHIVED_RULES = {
    # partner_ids of the mailing contacts came from mass_mailing_contact_partner,
    # which is not available for Odoo 18
    ("My mailing lists", "contact_id.partner_ids"),
}
# Rules of Odoo modules loaded as noupdate, kept with their v14 domain
FIXED_XMLIDS = {
    "sale.sale_order_line_rule_portal": (
        "[('order_id.message_partner_ids', 'child_of', "
        "[user.commercial_partner_id.id])]"
    ),
}
# Rules no longer defined by their module in Odoo 18, on fields that are gone
ARCHIVED_XMLIDS = (
    "mail.mail_notification_read_write_own",
    "payroll.hr_payslip_input_rule_company",
)


@openupgrade.migrate()
def migrate(env, version):
    cr = env.cr
    for (name, field), domain in FIXED_RULES.items():
        cr.execute(
            "UPDATE ir_rule SET domain_force = %s "
            "WHERE name = %s AND domain_force LIKE %s RETURNING id",
            (domain, name, f"%{field}%"),
        )
        _log(cr, "Fixed the domain of record rule %s %s", name)
    for name, field in ARCHIVED_RULES:
        cr.execute(
            "UPDATE ir_rule SET active = FALSE "
            "WHERE name = %s AND domain_force LIKE %s AND active RETURNING id",
            (name, f"%{field}%"),
        )
        _log(cr, "Archived record rule %s %s", name)
    for xmlid, domain in FIXED_XMLIDS.items():
        rule = env.ref(xmlid, raise_if_not_found=False)
        if rule and rule.domain_force != domain:
            rule.domain_force = domain
            _logger.info("Fixed the domain of record rule %s", xmlid)
    for xmlid in ARCHIVED_XMLIDS:
        rule = env.ref(xmlid, raise_if_not_found=False)
        if rule and rule.active:
            rule.active = False
            _logger.info("Archived record rule %s", xmlid)
    _remove_portal_from_internal_users(env)
    env["ir.rule"].invalidate_model()
    env.registry.clear_cache()


def _remove_portal_from_internal_users(env):
    internal = env.ref("base.group_user")
    portal = env.ref("base.group_portal")
    env.cr.execute(
        """
        DELETE FROM res_groups_users_rel portal_rel
        WHERE portal_rel.gid = %s
        AND EXISTS (
            SELECT 1 FROM res_groups_users_rel internal_rel
            WHERE internal_rel.uid = portal_rel.uid AND internal_rel.gid = %s
        )
        RETURNING (SELECT login FROM res_users WHERE id = portal_rel.uid)
        """,
        (portal.id, internal.id),
    )
    for (login,) in env.cr.fetchall():
        _logger.info("Removed the portal group of internal user %s", login)
    env["res.users"].invalidate_model(["groups_id"])
    env["res.groups"].invalidate_model(["users"])


def _log(cr, message, name):
    for (rule_id,) in cr.fetchall():
        _logger.info(message, rule_id, name)
