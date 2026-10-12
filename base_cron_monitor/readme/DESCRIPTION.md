Monitors the executions of server actions, which includes scheduled actions
and the actions of automation rules. Every execution is logged with the user
who ran it, its duration and the error raised, if any.

Logs are kept even when the transaction of the action is rolled back, so
failing scheduled actions and automation rules are logged with their
traceback.

To keep the volume low, the successful executions of the same action by the
same user in the same transaction are grouped in one log, with the number of
executions, the total duration and the longest execution. An automation rule
running on 1000 records gives one log, not 1000. Each failed execution has its
own log.

**How the logs are written**

Writing to the database while the monitored transaction is still running
froze the database in the 14.0 version: the log was written from a second
connection that could wait for a lock held by the monitored transaction,
which itself waited for the log to be written. PostgreSQL cannot detect such a
deadlock, so the locks were never released.

This version never writes during the monitored transaction:

- During the transaction, the executions are only collected in memory.
- Once the transaction is committed, rolled back, or its cursor is closed, the
  logs are inserted with a single SQL query, in a new and short transaction.
- The insert doesn't go through the ORM, so it can't trigger automation rules
  (which would be monitored in turn) or any other side effect.
- The insert waits at most 2 seconds for a lock. If the logs can't be written,
  they are dropped with a warning in the server log, and the monitored action
  is not affected.
- `queue_job` is not used anymore.
