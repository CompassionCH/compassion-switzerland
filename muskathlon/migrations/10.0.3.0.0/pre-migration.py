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


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    if not version:
        return

    openupgrade.load_xml()

    # Muskathlon registration will become event.registration object:
    # Prepare required columns
    if not openupgrade.column_exists(env.cr, 'event_registration', 'lead_id'):
        env.cr.execute("""
            ALTER TABLE event_registration ADD COLUMN lead_id integer;
            ALTER TABLE event_registration
                ADD COLUMN sport_discipline_id integer;
            ALTER TABLE event_registration
                ADD COLUMN sport_level character varying;
            ALTER TABLE event_registration
                ADD COLUMN sport_level_description text;
            ALTER TABLE event_registration ADD COLUMN amount_objective integer;
            ALTER TABLE event_registration
                ADD COLUMN website_published boolean;
            ALTER TABLE event_registration ADD COLUMN reg_id character varying;
            ALTER TABLE event_registration ADD COLUMN backup_id integer;
        """)
    # Insert data for events with registrations open
    events = env['crm.event.compassion'].search([
        ('odoo_event_id', '!=', False),
    ])
    env.cr.execute(
        """INSERT INTO event_registration(create_date,write_uid,
partner_id,create_uid,event_id,company_id,state,email,phone,write_date,origin,
name,date_open,lead_id,sport_discipline_id,sport_level,sport_level_description,
amount_objective,website_published,reg_id,backup_id)

SELECT now(),1,r.partner_id,1,odoo_event_id,1,'draft',p.email,p.phone,now(),
    'Registration automatically migrated',p.name,r.create_date,r.lead_id,
    sport_discipline_id,sport_level,sport_level_description,r.amount_objective,
    r.website_published,reg_id,r.id
    FROM muskathlon_registration r
    JOIN crm_event_compassion e ON r.event_id = e.id
    JOIN res_partner p ON r.partner_id = p.id
    WHERE event_id = ANY(%s)""", [events.ids]
    )
    # Update relations to registration
    table_names = ['account_invoice_line', 'recurring_contract',
                   'payment_transaction']
    env.cr.execute("""
        ALTER TABLE payment_transaction
        RENAME COLUMN registration_id TO muskathlon_registration_id;
        ALTER table payment_transaction
        DROP CONSTRAINT IF EXISTS payment_transaction_registration_id_fkey;
    """)
    for table in table_names:
        env.cr.execute("""
            ALTER table %s
            DROP CONSTRAINT IF EXISTS %s_muskathlon_registration_id_fkey;
        """ % (table, table))
        env.cr.execute("""
            UPDATE %s
            SET muskathlon_registration_id = (
                SELECT id FROM event_registration
                WHERE backup_id = muskathlon_registration_id
            );
        """ % table)
    env.cr.execute("""
        ALTER TABLE payment_transaction
        RENAME COLUMN muskathlon_registration_id TO registration_id;
    """)

    openupgrade.rename_fields(env, [
        ('account.invoice.line', 'account_invoice_line',
         'muskathlon_registration_id', 'registration_id'),
        ('recurring.contract', 'recurring_contract',
         'muskathlon_registration_id', 'registration_id'),
        ('crm.event.compassion', 'crm_event_compassion',
         'muskathlon_registration_ids', 'registration_ids'),
        ('res.partner', 'res_partner',
         'muskathlon_registration_ids', 'registration_ids'),
    ])
