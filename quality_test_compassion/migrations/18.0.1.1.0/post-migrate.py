from openupgradelib import openupgrade

from odoo import Command

STEP_NAME = "Test procedure"
EXPECTED_RESULT_NAME = "The test procedure completed as described"


@openupgrade.migrate()
def migrate(env, version):
    _convert_descriptions(env)
    _create_missing_versions(env)
    _freeze_missing_procedures(env)
    _fill_run_procedures(env)


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
    gets its own frozen copy of it. The descriptions are dropped once
    converted.
    """
    env.cr.execute("SELECT id, description FROM quality_test")
    descriptions = dict(env.cr.fetchall())
    step_vals = [
        _step_vals(test_id, description)
        for test_id, description in descriptions.items()
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
    for table in ("quality_test", "quality_test_version"):
        openupgrade.logged_query(
            env.cr, f"ALTER TABLE {table} DROP COLUMN IF EXISTS description"
        )


def _create_missing_versions(env):
    """Record the versions the tests and their runs refer to.

    A version was only recorded when a test was activated, so tests that were
    already active when versions appeared refer to a version that has no
    record, and would be left without any procedure to follow.
    """
    env.cr.execute("SELECT test_id, version FROM quality_test_version")
    existing = set(env.cr.fetchall())
    env.cr.execute(
        """
        SELECT id, test_version FROM quality_test
        WHERE state = 'active' AND test_version IS NOT NULL
        UNION
        SELECT test_id, tested_at_version FROM quality_test_run
        WHERE tested_at_version IS NOT NULL
        """
    )
    missing = sorted(set(env.cr.fetchall()) - existing)
    env["quality.test.version"].create(
        [{"test_id": test_id, "version": version} for test_id, version in missing]
    )


def _freeze_missing_procedures(env):
    """Copy the procedure of the tests into the versions holding none."""
    versions = env["quality.test.version"].search([("step_ids", "=", False)])
    steps_by_test = _steps_by_test(env)
    env["quality.test.step"].create(
        [
            {
                "test_id": version.test_id.id,
                "version_id": version.id,
                "sequence": step.sequence,
                "name": step.name,
                "description": step.description,
                "expected_result_ids": [
                    Command.create(
                        {"sequence": expected.sequence, "name": expected.name}
                    )
                    for expected in step.expected_result_ids
                ],
            }
            for version in versions
            for step in steps_by_test.get(version.test_id.id, [])
        ]
    )


def _fill_run_procedures(env):
    """Give past test runs the procedure they tested, with its known outcome."""
    steps_by_version = {}
    for step in env["quality.test.step"].search([("version_id", "!=", False)]):
        key = (step.test_id.id, step.version_id.version)
        steps_by_version.setdefault(key, []).append(step)
    steps_by_test = _steps_by_test(env)

    runs = env["quality.test.run"].search([])
    runs.fail_notification_sent = True
    for run in runs:
        steps = steps_by_version.get(
            (run.test_id.id, run.tested_at_version)
        ) or steps_by_test.get(run.test_id.id, [])
        run.step_ids = _run_step_commands(steps, run.result)


def _steps_by_test(env):
    """Return the steps currently edited on each test, by test id."""
    steps_by_test = {}
    for step in env["quality.test.step"].search([("version_id", "=", False)]):
        steps_by_test.setdefault(step.test_id.id, []).append(step)
    return steps_by_test


def _run_step_commands(steps, result):
    """Build the procedure of a run, every expected result bearing its outcome.

    The vals are written here rather than taken from the model, so that this
    script keeps behaving the same however the models evolve afterwards.
    """
    return [
        Command.create(
            {
                "step_id": step.id,
                "sequence": position,
                "name": step.name,
                "description": step.description,
                "result_ids": [
                    Command.create(
                        {
                            "expected_result_id": expected.id,
                            "sequence": index,
                            "name": expected.name,
                            "result": result,
                        }
                    )
                    for index, expected in enumerate(step.expected_result_ids)
                ],
            }
        )
        for position, step in enumerate(steps)
    ]
