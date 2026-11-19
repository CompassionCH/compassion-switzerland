##############################################################################
#
#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging

_logger = logging.getLogger(__name__)

# Records of databases migrated from 14.0 taken over by this module instead of
# being created again: (former module, name)
TAKEN_OVER = [
    ("l10n_ch_hr_payroll", "PROVISION_13"),
    ("hr_switzerland", "employee_tag_office"),
    ("hr_switzerland", "employee_tag_church_rep"),
]


def pre_init_hook(env):
    """On a database migrated from 14.0, the 13th salary rule (former module
    l10n_ch_hr_payroll) and the employee tags (former hr_switzerland) exist
    already, as do the columns of the contract (full-time wage, occupation
    rate...): this module takes them over."""
    cr = env.cr
    for module, name in TAKEN_OVER:
        cr.execute(
            """UPDATE ir_model_data SET module = 'hr_switzerland_13th_salary'
               WHERE module = %s AND name = %s
                 AND NOT EXISTS (
                     SELECT 1 FROM ir_model_data
                     WHERE module = 'hr_switzerland_13th_salary' AND name = %s)""",
            (module, name, name),
        )
        if cr.rowcount:
            _logger.info("%s.%s taken over", module, name)
