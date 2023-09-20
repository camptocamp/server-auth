# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import models


class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"

    def button_cancel_reconciliation(self):
        res = super().button_cancel_reconciliation()
        if self.env.context.get("force_partner_removal"):
            self.write({"partner_id": False, "partner_name": ""})
        return res
