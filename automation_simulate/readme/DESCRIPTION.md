Adds a **Simulate process** action on every model that has active automation
rules or scheduled actions, to test them on demand on a test database.

- **Automation rule**: the actions of the rule are run on the selected records,
  as superuser, without checking the trigger, the time window or the domain of
  the rule.
- **Scheduled action**: the whole scheduled action is run, as its own user, like
  the *Run Manually* button. The selected records are ignored.

The actions really run: never use this on real data.
