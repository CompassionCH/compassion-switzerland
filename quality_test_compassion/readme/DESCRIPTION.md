Allows teams to define quality tests for critical business processes and
track their test runs over time.

Each quality test has a name, HTML description, a responsible user, and an
employee department. Optionally, it can be linked to installed Odoo modules
so that developers know which modules affect the test outcome.

A test run can be created with one click and records the date, a pass/fail
result, and free-form notes. When a test fails, the responsible can open a
project task directly from the run record to track the fix. Each test run
also snapshots the installed versions of all related modules, making it easy
to correlate failures with specific module versions.

Notification rules can be configured per quality test:

- **Delay rule**: sends an email to the responsible when no test run has been
  recorded within a configurable number of days.
- **Module update rule**: sends an email when one of the related modules has
  been updated since the last test run.

Both rules are evaluated daily by a scheduled action.
