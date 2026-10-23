##############################################################################
#
#    Copyright (C) 2025 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#
#    The licence is in the file __manifest__.py
#
##############################################################################

import base64
import csv
from io import StringIO

from markupsafe import Markup

from odoo import _, fields, models
from odoo.exceptions import UserError

# Columns of the GMC export that we use to link letters and gifts
LETTER_COLUMN = "comm record"
GIFT_COLUMN = "gift name"


class GiftLetterImportWizard(models.TransientModel):
    """Import the CSV files sent by GMC that tell which gift each thank you
    letter is related to. GMC does not send us this link in the messages we
    receive, so without this file the gift can only be estimated.
    """

    _name = "gift.letter.import.wizard"
    _description = "Import gift links of thank you letters"

    data = fields.Binary("GMC file", required=True)
    filename = fields.Char()
    result = fields.Html(readonly=True)

    def import_file(self):
        self.ensure_one()
        rows = self._read_file()
        kit_identifiers, gmc_gift_ids = zip(*rows, strict=False)
        letters = self.env["correspondence"].search(
            [("kit_identifier", "in", list(kit_identifiers))]
        )
        letter_per_kit = {letter.kit_identifier: letter for letter in letters}
        gifts = self.env["sponsorship.gift"].search(
            [("gmc_gift_id", "in", list(gmc_gift_ids))]
        )
        gift_per_gmc_id = {gift.gmc_gift_id: gift for gift in gifts}

        updated = 0
        issues = []
        for kit_identifier, gmc_gift_id in rows:
            letter = letter_per_kit.get(kit_identifier)
            gift = gift_per_gmc_id.get(gmc_gift_id)
            if not letter:
                issues.append(_("No letter found with kit id %s") % kit_identifier)
                continue
            if not gift:
                issues.append(
                    _("No gift found with GMC id %(gift)s (letter %(letter)s)")
                    % {"gift": gmc_gift_id, "letter": kit_identifier}
                )
                continue
            if gift.sponsorship_id != letter.sponsorship_id:
                # GMC is the reference, we link them anyway but warn the user
                issues.append(
                    _(
                        "Letter %(letter)s and gift %(gift)s are not on the "
                        "same sponsorship. They were linked nevertheless."
                    )
                    % {"letter": kit_identifier, "gift": gmc_gift_id}
                )
            if letter.verified_gift_id == gift:
                continue
            letter.verified_gift_id = gift
            updated += 1

        self.result = self._format_result(len(rows), updated, issues)
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }

    def _read_file(self):
        """Extract the letter and gift references of the GMC file.
        :return: list of tuples (kit_identifier, gmc_gift_id)
        """
        content = base64.b64decode(self.data)
        for encoding in ("utf-8-sig", "cp1252"):
            try:
                text = content.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        else:
            raise UserError(_("The encoding of the file is not supported."))

        reader = csv.DictReader(StringIO(text), delimiter=";")
        reader.fieldnames = [name.strip().lower() for name in reader.fieldnames or []]
        missing_columns = {LETTER_COLUMN, GIFT_COLUMN} - set(reader.fieldnames)
        if missing_columns:
            raise UserError(
                _("The following columns are missing in the file: %s")
                % ", ".join(sorted(missing_columns))
            )

        rows = []
        for row in reader:
            kit_identifier = (row.get(LETTER_COLUMN) or "").strip()
            gmc_gift_id = (row.get(GIFT_COLUMN) or "").strip()
            if kit_identifier and gmc_gift_id:
                rows.append((kit_identifier, gmc_gift_id))
        if not rows:
            raise UserError(_("No data was found in the file."))
        return rows

    def _format_result(self, total, updated, issues):
        result = Markup("<p>{}</p>").format(
            _(
                "%(total)s lines read, %(updated)s letters updated, "
                "%(issues)s issues."
            )
            % {"total": total, "updated": updated, "issues": len(issues)}
        )
        if issues:
            result += Markup("<ul>{}</ul>").format(
                Markup("").join(Markup("<li>{}</li>").format(issue) for issue in issues)
            )
        return result
