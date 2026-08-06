from openupgradelib import openupgrade

from odoo import Command

STEP_NAME = "Test procedure"
EXPECTED_RESULT_NAME = "The test procedure completed as described"


@openupgrade.migrate()
def migrate(env, version):
    _convert_descriptions(env)
    _fill_run_results(env)


def _step_vals(test_id, description):
    """Build the single step replacing a free-form description."""
    return {
        "test_id": test_id,
        "name": STEP_NAME,
        "description": description,
        "expected_result_ids": [Command.create({"name": EXPECTED_RESULT_NAME})],
    }


def _convert_descriptions(env):
    """Move every free-form description into a single test step.

    Each test gets the step it is now edited with, and each activated version
    gets its own frozen copy of it.
    """
    env.cr.execute("SELECT id, description FROM quality_test")
    descriptions = dict(env.cr.fetchall())
    step_vals = [
        _step_vals(test_id, description) for test_id, description in descriptions.items()
    ]
    env.cr.execute("SELECT id, test_id, description FROM quality_test_version")
    for version_id, test_id, description in env.cr.fetchall():
        step_vals.append(
            dict(
                _step_vals(test_id, description or descriptions.get(test_id)),
                version_id=version_id,
            )
        )
    env["quality.test.step"].create(step_vals)


def _fill_run_results(env):
    """Give past test runs the result lines of the procedure they tested."""
    runs = env["quality.test.run"].search([])
    runs.fail_notification_sent = True
    for run in runs:
        previous_result = run.result
        run.result_ids = run.test_id._get_run_result_commands(run.tested_at_version)
        run.result_ids.write({"result": previous_result})
