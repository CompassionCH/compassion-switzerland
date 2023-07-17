from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    if not version:
        return

    # Update A4 Compassion to A4 l10n_ch
    env.cr.execute(
        """
        UPDATE report_paperformat_parameter
        SET paperformat_id = 21
        WHERE paperformat_id IN (19,9,8,7)
    """
    )
    env.cr.execute(
        """
        UPDATE partner_communication_job
        SET config_id = 1
        WHERE config_id IN (29)
    """
    )
    openupgrade.set_xml_ids_noupdate_value(
        env,
        "report_compassion",
        [
            "report_bvr_fund",
            "bvr_fund",
            "report_bvr_fund_document",
            "report_bvr_gift_sponsorship",
            "report_2bvr_gift_sponsorship",
            "bvr_gift_sponsorship_2bvr",
            "2bvr_gift_sponsorship",
            "report_bvr_sponsorship_gift_document_2bvr",
            "bvr_gift_sponsorship",
            "report_bvr_sponsorship_gift_document",
            "report_sponsorship_2bvr_top_slip",
            "report_sponsorship_2bvr_bottom_slip",
            "report_bvr_sponsorship",
            "report_2bvr_sponsorship",
            "report_bvr_due",
            "bvr_sponsorship",
            "report_bvr_sponsorship_document",
            "report_gift_document",
            "bvr_sponsorship_2bvr",
            "2bvr_sponsorship",
            "report_bvr_sponsorship_document_2bvr",
            "report_gift_document_2bvr",
            "bvr_due",
            "report_bvr_due_document",
            "report_partner_communication_mailing_bvr",
            "partner_communication_mailing_bvr",
            "paperformat_childpack",
            "paperformat_mini_childpack",
            "paperformat_a4_childpack",
            "style",
            "paperformat_anniversary_card",
            "tax_receipt_report",
            "tax_receipt",
        ],
        False,
    )
