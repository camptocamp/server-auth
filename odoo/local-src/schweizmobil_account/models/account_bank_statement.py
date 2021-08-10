# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import api, models


class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"

    @api.model
    def create(self, vals):
        if 'partner_id' in vals:
            vals['partner_id'] = False
        line = super(AccountBankStatementLine, self).create(vals)
        return line
