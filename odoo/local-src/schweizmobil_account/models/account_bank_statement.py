# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import api, fields, models


class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"

    partner_name_alternate = fields.Char(
        string="Altername partnername", required=True
    )

    @api.model
    def create(self, vals):
        if 'partner_id' in vals:
            vals['partner_id'] = False
        if 'partner_name' in vals:
            vals['partner_name_alternate'] = vals['partner_name']
            vals['partner_name'] = False
        line = super(AccountBankStatementLine, self).create(vals)
        return line
