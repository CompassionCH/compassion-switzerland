##############################################################################
#
#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models


class EbicsFile(models.Model):
    _inherit = "ebics.file"

    def _create_bank_statement_oca(self, res, st_data):
        """Import each statement of the EBICS file in a separate job,
        as large statements are too slow to be imported in one go."""
        data = st_data["data"]
        job_data = dict(
            st_data, data=data.decode() if isinstance(data, bytes) else data
        )
        self.with_delay_sh(
            "_import_bank_statement_job",
            job_data,
            description=f"Import bank statement {st_data['acc_number']} "
            f"from EBICS file {self.name}",
        )
        res["notifications"].append(
            {
                "type": "warning",
                "message": self.env._(
                    "The statement for Account Number %(nr)s is imported "
                    "in a background job.",
                    nr=st_data["acc_number"],
                ),
            }
        )

    def _import_bank_statement_job(self, st_data):
        """Job importing a single statement and linking it to the EBICS file."""
        self.ensure_one()
        self = self.with_context(allowed_company_ids=self.env.user.company_ids.ids)
        res = {"statement_ids": [], "notifications": []}
        super()._create_bank_statement_oca(res, st_data)
        self._process_download_result(res, file_format=self.download_process_method)
        return self.note_process
