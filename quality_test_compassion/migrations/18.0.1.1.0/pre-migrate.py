from openupgradelib import openupgrade

MAIL_TEMPLATE_XML_IDS = [
    "email_template_quality_test_notification",
    "email_template_quality_test_run_fail",
]


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.set_xml_ids_noupdate_value(
        env, "quality_test_compassion", MAIL_TEMPLATE_XML_IDS, False
    )
    _renumber_duplicated_tests(env)


def _renumber_duplicated_tests(env):
    """Renumber the tests sharing their number with another one.

    Duplicating a test used to copy its number, which is now forbidden by a
    uniqueness constraint. The oldest test of each group keeps its number.
    """
    env.cr.execute(
        """
        SELECT id FROM (
            SELECT id, ROW_NUMBER() OVER (
                PARTITION BY sequence ORDER BY id
            ) AS position
            FROM quality_test
            WHERE sequence IS NOT NULL
        ) numbered
        WHERE position > 1
        ORDER BY id
        """
    )
    for (test_id,) in env.cr.fetchall():
        openupgrade.logged_query(
            env.cr,
            "UPDATE quality_test SET sequence = %s WHERE id = %s",
            (env["ir.sequence"].next_by_code("QTSEQ"), test_id),
        )
