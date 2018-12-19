# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from openupgradelib import openupgrade


def migrate(cr, version):
    if not version:
        return

    def add_communication_record(config_name, template_name, config_xmlid,
                                 template_xmlid):
        """
        Map a communication record to a XML record.
        :param config_name: Name of the communication.config record.
        :param template_name: Name of the mail.template record.
        :param config_xmlid: XMLID of the communication.config record.
        :param template_xmlid: XMLID of the mail.template record.
        :return: Nothing
        """
        cr.execute("""
            SELECT c.id
            FROM partner_communication_config c
                JOIN utm_source s ON c.source_id = s.id
            WHERE s.name ILIKE %s
        """, ['%' + config_name + '%'])
        config_id = cr.fetchone()
        if config_id:
            openupgrade.add_xmlid(
                cr,
                module='partner_communication_switzerland',
                xmlid=config_xmlid,
                model='partner.communication.config',
                res_id=config_id[0],
                noupdate=True
            )

        cr.execute("""
            SELECT id
            FROM mail_template
            WHERE name ILIKE %s
        """, ['%' + template_name + '%'])
        template_id = cr.fetchone()
        if template_id:
            openupgrade.add_xmlid(
                cr,
                module='partner_communication_switzerland',
                xmlid=template_xmlid,
                model='mail.template',
                res_id=template_id[0],
                noupdate=True
            )

    # Add WRPR New Dossier records
    add_communication_record('Sponsorship - New Dossier Write&Pray',
                             'New Dossier - Write&Pray',
                             'sponsorship_dossier_wrpr',
                             'email_wrpr_dossier')

    # Add WRPR Reminder records
    add_communication_record('Write&Pray reminder',
                             'Write&Pray reminder',
                             'sponsorship_wrpr_reminder',
                             'email_wrpr_reminder')
