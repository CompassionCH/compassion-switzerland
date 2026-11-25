A manual distribution (module `account_analytic_distribution_manual`) is a
named analytic distribution, an allocation key such as "ADM 30 % / Fundraising
70 %". This module keeps the records that use it in sync: when the
distribution of a manual distribution changes, the employee contracts, assets
and asset profiles that use it get the new distribution. The journal items
already posted keep theirs.

On a database migrated from 14.0, the installation turns each analytic tag
with a distribution into a manual distribution of the same name, and gives it
to the assets and asset profiles that had the tag.
