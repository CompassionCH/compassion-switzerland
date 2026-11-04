import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)


@openupgrade.migrate()
def migrate(env, version):
    """T3651: align the website visitors linked to a partner with the 18.0
    format, where the access token of such a visitor is the partner id.

    Visitors coming from older versions are linked to a partner but keep a
    32 chars hexadecimal token. This makes the partner merge wizard crash
    (invalid input syntax for type integer) and would drop the partner link
    as soon as the token is written, since `partner_id` is computed from it.
    """
    cr = env.cr
    Visitor = env["website.visitor"].sudo()

    # The token must be unique: keep only the latest visitor of each partner.
    cr.execute(
        """
        SELECT partner_id, array_agg(
                   id ORDER BY last_connection_datetime DESC NULLS LAST, id DESC)
          FROM website_visitor
         WHERE partner_id IS NOT NULL
         GROUP BY partner_id
        HAVING count(*) > 1
        """
    )
    duplicates = cr.fetchall()
    for _partner_id, visitor_ids in duplicates:
        target = Visitor.browse(visitor_ids[0])
        Visitor.browse(visitor_ids[1:])._merge_visitor(target)
    _logger.info("Merged the extra visitors of %s partners", len(duplicates))

    # Direct SQL: writing the token would recompute the stored partner_id.
    openupgrade.logged_query(
        cr,
        """
        UPDATE website_visitor
           SET access_token = partner_id::text
         WHERE partner_id IS NOT NULL
           AND access_token != partner_id::text
        """,
    )
    env.invalidate_all()
