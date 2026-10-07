This module speeds up the processing of EBICS files with the OCA bank
statement import modules.

When an EBICS file is processed, `account_ebics` splits it into one
CAMT file per bank account statement. Instead of importing all of them
in the same transaction, this module imports each statement in a
separate background job (using `with_delay_sh` from `queue_job_optional`).

Each job imports its statement, links it to the EBICS file and appends
the import results to the processing notes of the EBICS file.
