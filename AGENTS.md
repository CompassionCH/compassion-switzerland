# Compassion Switzerland · Odoo 18

These addons extend sponsorships, communications and accounting for Compassion
Switzerland. Only the Swiss deployment has them, and it runs Odoo Community. Some also
serve the Polish office, which the Swiss deployment hosts.

## Dependencies and translations

Declare the addons you use in the manifest's `depends`. Odoo refuses a dependency cycle
between addons: check the whole chain before adding a dependency on another repository's
addon. Addons here can depend on `compassion-modules`, `compassion-accounting` and
`compassion-website`. Shared addons never depend on addons here: the existing exception
is `compassion-website`'s `crowdfunding_compassion`, which depends on
`partner_communication_switzerland`, so a change there can break it. Put new Swiss
behavior here, for example by overriding a base hook as `sbc_switzerland` does.

If the module has catalogs, update its existing locales. For its first catalogs, use
Switzerland's `fr_CH`, `de_DE`, `it_IT`. The Polish office, which the Swiss deployment
hosts, uses `pl_PL`: add it when the module shows text to the Polish office's sponsors.
Ask the maintainer if coverage is unclear.

## Where to find the rules

When a task changes code here, open the shared rule subjects it needs. If the toolkit
plugins are available, use their skills `code-rules:rules` and `odoo-rules:rules`;
otherwise fetch the published rules into a temporary folder:
`(d="$(mktemp -d)" && git clone -q --depth 1 --branch main https://github.com/CompassionCH/compassion-agent-toolkit.git "$d" && echo "$d")`.
There, each index is `plugins/<plugin>/skills/rules/SKILL.md`. If the sandbox blocks the
network, ask the user to run the command, or read the indexes online:
[code-rules](https://github.com/CompassionCH/compassion-agent-toolkit/blob/main/plugins/code-rules/skills/rules/SKILL.md)
[odoo-rules](https://github.com/CompassionCH/compassion-agent-toolkit/blob/main/plugins/odoo-rules/skills/rules/SKILL.md)

## Before opening a PR

Run `pre-commit run` on staged files, or `pre-commit install` to enable the hooks on
commit. CI covers static checks only. It runs
`SKIP=oca-gen-addon-readme pre-commit run --all-files --show-diff-on-failure --color=always`
and checks for untracked generated files. Run the affected Odoo tests separately.

Then run the rules review in `review.md`, linked from the code-rules index. Use the
`code-rules:rules-reviewer` subagent when the plugin is available; otherwise give a
fresh read-only session the published reviewer prompt,
`plugins/code-rules/agents/rules-reviewer.md` in that folder
([online](https://github.com/CompassionCH/compassion-agent-toolkit/blob/main/plugins/code-rules/agents/rules-reviewer.md)).
Only if neither is possible, say in the PR description that no rules review ran. Record
findings, coverage gaps and their disposition there.
