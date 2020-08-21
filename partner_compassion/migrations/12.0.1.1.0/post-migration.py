from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, installed_version):
    if not installed_version:
        return

    # Store criminal records in partners
    crimis = env["ir.attachment"].search([("name", "ilike", "Criminal record")])
    to_del = env["ir.attachment"]
    for crimi in crimis:
        attached_record = env[crimi.res_model].browse(crimi.res_id)
        if attached_record.exists() and crimi.datas:
            if hasattr(attached_record, "partner_id"):
                attached_record.partner_id.criminal_record = crimi.datas
                attached_record.partner_id.criminal_record_date = \
                    attached_record.create_date.date()
                to_del += crimi
    to_del.unlink()
