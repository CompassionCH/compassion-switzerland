# Copyright 2026 Compassion CH (http://www.compassion.ch)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


def post_init_hook(env):
    env["automation.simulate.target"]._sync()


def uninstall_hook(env):
    env["ir.actions.act_window"].search(
        [("res_model", "=", "automation.simulate.wizard")]
    ).unlink()
