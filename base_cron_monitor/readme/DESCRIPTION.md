Monitors the server actions, scheduled actions and automation rules: every
execution is logged with its user, duration and error, if any.

- The logs can be filtered, grouped and analysed (list, pivot and graph views),
  in *Settings > Technical > Automation > Server Action Monitor*, or with the
  *Executions* button of server actions, scheduled actions and automation rules.
- Logs are kept even if the transaction of the action is rolled back.
- The successful executions of an action by a user in the same transaction are
  grouped in one log (e.g. an automation rule running on 1000 records).

The logs are written only once the transaction of the action is over (committed
or rolled back), in one query and in a separate short transaction. The
monitoring never writes to the database while the monitored transaction holds
its locks, which avoids the deadlocks of the previous versions.
