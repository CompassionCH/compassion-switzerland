- The logs are lost if they can't be written after the transaction (lock
  timeout, database connection pool full, server killed before the end of the
  transaction).
- When an action runs other server actions (e.g. multi actions), each of them
  is logged and their durations overlap.
- The actions of automation rules triggered by onchanges in the user interface
  are logged as well.
