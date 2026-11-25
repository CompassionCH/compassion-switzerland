This module splits the salaries of an employee among analytic accounts: the
employee contract gets an analytic distribution (for example ADM 30 % /
Fundraising 70 %), given to the income and expense lines of the journal entry
of each payslip. The balance sheet lines get no analytic distribution.

Without distribution on the contract, the analytic account of the contract or
of the salary rule is used, as in `payroll_account`.

The distribution of a contract usually comes from a manual distribution (an
allocation key such as "HR-ADM", module `account_analytic_distribution_manual`):
a change of the key goes to all its contracts
(`account_analytic_distribution_manual_sync`).

On a database migrated from 14.0, the installation gives each contract the
manual distribution made of its former analytic tag.

When `quality_test_compassion` is installed, the installation also creates the
quality test "Payroll: payslips and their analytic split", linked to the
payroll modules: its responsible is notified to check the payroll split after
each update of these modules.
