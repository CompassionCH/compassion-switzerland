This module fills in the **PR URI** field of a task automatically when a pull
request is opened, or renamed, on any repository of the GitHub organisation.

The task is identified by its code (`T0000`), which is read at the beginning of
the pull request title, or at the beginning of the branch name.

| Pull request                       | Linked task |
| ---------------------------------- | ----------- |
| `[T1601] Use the GitHub REST API`  | `T1601`     |
| `T1601 Use the GitHub REST API`    | `T1601`     |
| branch `T1601-use-github-rest-api` | `T1601`     |

A task that already carries a PR URI is left untouched.
