import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)


@openupgrade.migrate()
def migrate(env, version):
    """The standard 'account.report_invoice_with_payments' view (Invoice PDF)
    still holds the v14 Compassion arch in the database: it reads
    'l10n_ch_isr_number', which no longer exists, and calls the
    'report_invoice_document_with_swiss_qr' template that was dropped in the
    18.0 migration. Every invoice PDF (portal pay-online page, backend print)
    crashes with "AttributeError: 'account.move' object has no attribute
    'l10n_ch_isr_number'". The edited arch is flagged as user-modified, so
    upgrading 'account' never reloads it - reset it to the file version and
    remove the orphaned template.
    """
    view = env.ref("account.report_invoice_with_payments", raise_if_not_found=False)
    if view and "l10n_ch_isr_number" in (view.with_context(lang=None).arch_db or ""):
        view.reset_arch(mode="hard")
        _logger.info("T3523: reset account.report_invoice_with_payments arch")
    openupgrade.delete_records_safely_by_xml_id(
        env, ["report_compassion.report_invoice_document_with_swiss_qr"], True
    )
