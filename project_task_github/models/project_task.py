# Copyright 2026 Compassion CH
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging
import re

from odoo import api, models

_logger = logging.getLogger(__name__)

# The regular expression used to extract the task identifier.
# Some examples where we can extract "T1000" :
# - T1000 Name of the task
# - [T1000] Name of the task
TASK_CODE_RE = re.compile(r"^\W*(T\d+)\b", re.IGNORECASE)


class ProjectTask(models.Model):
    _inherit = "project.task"

    @api.model
    def _find_by_github_reference(self, *references):
        """Find the task a pull request refers to.

        :param references: strings that may start with a task code, tried in
            the given order. Typically the pull request title first, then the
            name of its branch as a fallback for sloppily titled requests.
        :return: the matching task, or an empty recordset.
        """
        for reference in references:
            match = TASK_CODE_RE.match(reference or "")
            if not match:
                continue
            code = match.group(1).upper()
            task = self.sudo().search([("code", "=", code)], limit=1)
            if task:
                return task
            _logger.info("Reference %s matches no task.", code)
        return self.browse()

    def _set_github_pr_uri(self, pr_uri):
        """Link a pull request to the tasks that have none yet.

        Tasks already linked to a pull request are left untouched.

        :return: the tasks that were actually linked.
        """
        linked = self.browse()
        for task in self:
            if task.pr_uri:
                _logger.info(
                    "Task %s is already linked to %s, ignoring %s.",
                    task.code,
                    task.pr_uri,
                    pr_uri,
                )
                continue
            task.sudo().write({"pr_uri": pr_uri})
            linked |= task
        return linked
