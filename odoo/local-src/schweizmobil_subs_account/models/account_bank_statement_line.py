# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import api, fields, models


class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"

    partner_name_alternate = fields.Char(string="Altername partnername")

    @api.model_create_multi
    def create(self, vals):
        if 'partner_id' in vals:
            vals['partner_id'] = False
        if 'partner_name' in vals:
            vals['partner_name_alternate'] = vals['partner_name']
            vals['partner_name'] = False
        line = super().create(vals)
        return line

    def action_undo_reconciliation(self):
        self.write({"partner_id": False, "partner_name": ""})
        return super().action_undo_reconciliation()
