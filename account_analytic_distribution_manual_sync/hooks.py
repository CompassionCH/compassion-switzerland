# Copyright 2026 Compassion CH (http://www.compassion.ch)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging

from odoo.tools import SQL

_logger = logging.getLogger(__name__)

# Relation tables of 14.0 between the analytic tags and the records that keep a
# distribution: (table, column of the record, model)
TAG_RELATIONS = [
    ("account_analytic_tag_account_asset_rel", "account_asset_id", "account.asset"),
    (
        "account_analytic_tag_account_asset_profile_rel",
        "account_asset_profile_id",
        "account.asset.profile",
    ),
]


def _table_exists(cr, table):
    cr.execute("SELECT to_regclass(%s)", (table,))
    return bool(cr.fetchone()[0])


def get_tag_distributions(env):
    """Manual distribution of each analytic tag with a distribution of a database
    migrated from 14.0 (tables account_analytic_tag and
    account_analytic_distribution): {tag id: manual distribution}."""
    cr = env.cr
    if not (
        _table_exists(cr, "account_analytic_tag")
        and _table_exists(cr, "account_analytic_distribution")
    ):
        return {}
    cr.execute(
        """SELECT t.id, t.name, d.account_id, d.percentage
           FROM account_analytic_tag t
           JOIN account_analytic_distribution d ON d.tag_id = t.id
           JOIN account_analytic_account a ON a.id = d.account_id
           ORDER BY t.id"""
    )
    tags = {}
    for tag_id, name, account_id, percentage in cr.fetchall():
        tags.setdefault(tag_id, (name, {}))[1][str(account_id)] = percentage
    manual_obj = env["account.analytic.distribution.manual"].with_context(
        active_test=False
    )
    result = {}
    for tag_id, (name, distribution) in tags.items():
        name = name.get("en_US") if isinstance(name, dict) else name
        result[tag_id] = _get_manual(manual_obj, name, distribution)
    return result


def _same_distribution(first, second):
    def normalize(distribution):
        return {
            key: round(float(value), 4) for key, value in (distribution or {}).items()
        }

    return normalize(first) == normalize(second)


def _get_manual(manual_obj, name, distribution):
    """The manual distribution of a tag: an existing one of the same name only
    when its distribution is the same (a re-run of the migration); otherwise a
    new one named "<tag> (14.0)", so neither allocation replaces the other."""
    candidates = [name] + [
        f"{name} (14.0)" if index == 1 else f"{name} (14.0) {index}"
        for index in range(1, 10)
    ]
    for candidate in candidates:
        manual = manual_obj.search(
            [("name", "=", candidate), ("company_id", "=", manual_obj.env.company.id)],
            limit=1,
        )
        if not manual:
            return manual_obj.create(
                {"name": candidate, "analytic_distribution": distribution}
            )
        if _same_distribution(manual.analytic_distribution, distribution):
            return manual
        _logger.warning(
            "Manual distribution %s exists with other percentages: not reused for "
            "the analytic tag %s",
            candidate,
            name,
        )
    raise ValueError(f"No free name for the manual distribution of the tag {name}")


def post_init_hook(env):
    """On a database migrated from 14.0, the assets and asset profiles get the
    manual distribution of their former analytic tag (and its distribution)."""
    manuals = get_tag_distributions(env)
    if not manuals:
        return
    cr = env.cr
    for table, column, model in TAG_RELATIONS:
        if model not in env or not _table_exists(cr, table):
            continue
        # Only the tags with a distribution: a record may also carry ordinary
        # tags, which are no allocation key
        cr.execute(
            SQL(
                "SELECT %s, min(account_analytic_tag_id) FROM %s"
                " WHERE account_analytic_tag_id = ANY(%s) GROUP BY 1",
                SQL.identifier(column),
                SQL.identifier(table),
                list(manuals),
            )
        )
        records = env[model].with_context(active_test=False)
        count = 0
        for res_id, tag_id in cr.fetchall():
            manual = manuals.get(tag_id)
            record = records.browse(res_id).exists()
            if manual and record:
                record.write(
                    {
                        "manual_distribution_id": manual.id,
                        "analytic_distribution": manual.analytic_distribution,
                    }
                )
                count += 1
        _logger.info("%s %s get the distribution of their analytic tag", count, model)
    _profile_keys(env)


def _profile_keys(env):
    """An asset profile without manual distribution takes the one most used by
    its assets; its assets without manual distribution that had the
    distribution of the profile take it too."""
    if "account.asset.profile" not in env:
        return
    assets = env["account.asset"].with_context(active_test=False)
    for profile in (
        env["account.asset.profile"]
        .with_context(active_test=False)
        .search([("manual_distribution_id", "=", False)])
    ):
        profile_assets = assets.search([("profile_id", "=", profile.id)])
        keys = profile_assets.manual_distribution_id
        if not keys:
            continue
        key = max(
            keys,
            key=lambda k, pa=profile_assets: len(
                pa.filtered(lambda a, k=k: a.manual_distribution_id == k)
            ),
        )
        old_distribution = profile.analytic_distribution
        profile.write(
            {
                "manual_distribution_id": key.id,
                "analytic_distribution": key.analytic_distribution,
            }
        )
        followers = profile_assets.filtered(
            lambda a, od=old_distribution: not a.manual_distribution_id
            and a.analytic_distribution == od
        )
        followers.write(
            {
                "manual_distribution_id": key.id,
                "analytic_distribution": key.analytic_distribution,
            }
        )
        _logger.info(
            "Asset profile %s and %s of its assets get the manual distribution %s",
            profile.name,
            len(followers),
            key.name,
        )
