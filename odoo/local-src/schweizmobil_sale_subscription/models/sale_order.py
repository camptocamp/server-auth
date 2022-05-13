# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import _, fields, models
from odoo.addons.stock.models.product import OPERATORS
from odoo.exceptions import UserError


class SaleOrder(models.Model):

    _name = "sale.order"
    _inherit = [
        "sale.order",
        "sale.payment.fields.mixin",
        "sale.payment.subscription.fields.mixin",
    ]

    customer_number = fields.Char(related="partner_id.customer_number")
    invoice_count = fields.Integer(search="_search_invoice_count")

    def _prepare_invoice(self):
        res = super()._prepare_invoice()
        res.update(
            {
                "invoicing_method": self.invoicing_method,
                "paid_online": self.paid_online,
            }
        )
        return res

    def _search_invoice_count(self, operator, value):
        if operator not in OPERATORS:
            raise UserError(_('Invalid domain operator %s') % operator)
        if not isinstance(value, (float, int)):
            raise UserError(_('Invalid domain right operand %s') % value)
        self.flush(["order_line"])
        self.env["sale.order.line"].flush(["invoice_lines"])
        self.env["account.move.line"].flush(["move_id"])
        self.env["account.move"].flush(["type"])
        self.env.cr.execute(
            r"""
            SELECT so.id, count(am.id)
                FROM sale_order so
                JOIN sale_order_line sol ON sol.order_id = so.id
                LEFT JOIN sale_order_line_invoice_rel soli_rel ON soli_rel.order_line_id = sol.id
                LEFT JOIN account_move_line aml ON aml.id = soli_rel.invoice_line_id
                LEFT JOIN account_move am ON am.id = aml.move_id
            GROUP BY so.id;"""
        )
        query_res = self.env.cr.fetchall()
        res = [
            tpl[0] for tpl in query_res if OPERATORS[operator](tpl[1], value)
        ]
        return [('id', 'in', res)]
