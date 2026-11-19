##############################################################################
#
#    Copyright (C) 2017 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from . import models


def uninstall_hook(env):
    # Put back the domain of the hr rule written by this module
    # (res.partner.bank._hr_switzerland_restrict_private_bank_accounts)
    rule = env.ref(
        "hr.ir_rule_res_partner_bank_internal_users", raise_if_not_found=False
    )
    if rule:
        rule.sudo().domain_force = "[('partner_id.employee_ids', '=', False)]"
