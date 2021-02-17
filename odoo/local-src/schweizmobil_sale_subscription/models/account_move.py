# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import fields, models


class AccountMove(models.Model):

    _name = "account.move"
    _inherit = ["account.move", "sale.payment.fields.mixin"]

    customer_number = fields.Char(related="partner_id.customer_number")
