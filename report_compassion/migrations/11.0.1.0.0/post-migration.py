from openupgradelib import openupgrade


def migrate(cr, version):
    if not version:
        return

    # Force upgrade the reports
    openupgrade.load_xml(cr, 'report_compassion', 'report/anniversary_card.xml')
    openupgrade.load_xml(cr, 'report_compassion', 'report/bvr_fund.xml')
    openupgrade.load_xml(cr, 'report_compassion', 'report/bvr_gift.xml')
    openupgrade.load_xml(cr, 'report_compassion', 'report/bvr_sponsorship.xml')
    openupgrade.load_xml(cr, 'report_compassion', 'report/childpack.xml')
    openupgrade.load_xml(
        cr, 'report_compassion', 'report/communication_mailing_bvr.xml')
    openupgrade.load_xml(cr, 'report_compassion', 'report/partner_communication.xml')
    openupgrade.load_xml(cr, 'report_compassion', 'report/tax_receipt.xml')
