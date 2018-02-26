# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2017 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Samuel Fringeli <samuel.fringeli@me.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from openupgradelib import openupgrade
import re

# on doit pouvoir faire en sorte que les mails déjà existants à qui on a envoyé
# des lettres se mettent automatiquement dans invalid emails, sauf si il y a
# déjà un nouveau mail remis

@openupgrade.migrate(use_env=True)
def migrate(env, version):
    if not version:
        return

    for subject in ['Ung_ltige Emailadresse', 'Adresse email invalide',
                    'Wrong e-mail address', 'Indirizzo non valido']:
        results = env['partner.communication.job']\
            .search([('subject', 'like', subject)])

        for result in results:
            try:
                body_html = result.body_html
                inv_mail = re.search(r'[\w\.-]+@[\w\.-]+', body_html).group(0)
                inv_mail = inv_mail[0:-1] if inv_mail[-1] == '.' else inv_mail
                partner = result.partner_id

                if inv_mail != 'info@compassion.ch' and not partner.email:
                    partner.invalid_mail = inv_mail

            except AttributeError:
                pass
