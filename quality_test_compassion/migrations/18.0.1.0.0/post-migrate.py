from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    for test in env["quality.test"].search([("sequence", "=", False)]):
        test.sequence = env["ir.sequence"].next_by_code("QTSEQ")
        test.test_run_ids.write(
            {
                "tested_at_version": test.test_version,
            }
        )
        if test.state == "active":
            env["quality.test.version"].create(
                {
                    "description": test.description,
                    "test_id": test.id,
                    "version": test.test_version,
                }
            )
