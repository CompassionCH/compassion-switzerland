##############################################################################
#
#    Copyright (C) 2014-2024 Compassion CH (http://www.compassion.ch)
#    @author: Jérémie Lang
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models


class CamtParser(models.AbstractModel):
    """Parser for camt bank statement import files."""

    _inherit = "account.statement.import.camt.parser"

    def parse_transaction_details(self, ns, node, transaction):
        super().parse_transaction_details(ns, node, transaction)
        found_node = node.xpath(
            "./ns:RmtInf/ns:Strd/ns:AddtlRmtInf", namespaces={"ns": ns}
        )
        if len(found_node) != 0:
            self.add_value_from_node(
                ns,
                node,
                ["./ns:RmtInf/ns:Strd/ns:AddtlRmtInf"],
                transaction,
                "additional_ref",
            )
