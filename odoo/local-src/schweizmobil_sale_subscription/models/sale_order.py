# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import _, api, fields, models
from odoo.addons.stock.models.product import OPERATORS
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero


class SaleOrder(models.Model):

    _name = "sale.order"
    _inherit = [
        "sale.order",
        "sale.payment.fields.mixin",
        "sale.payment.subscription.fields.mixin",
    ]

    customer_number = fields.Char(related="partner_id.customer_number")
    invoice_count = fields.Integer(search="_search_invoice_count")

    @api.constrains("online_renewal")
    def _check_payment_status(self):
        for rec in self:
            unpaid_inv = rec.invoice_ids.filtered(
                lambda i: i.invoice_payment_state
                in ("not_paid", "partially_paid")
                and i.state == "posted"
            )

            if unpaid_inv:
                raise ValidationError(
                    _(
                        "All related posted invoices should be paid\n%s"
                        % ", ".join(unpaid_inv.mapped("name"))
                    )
                )

    def _prepare_invoice(self):
        res = super()._prepare_invoice()
        if self.online_renewal == "ios_iap":
            report_to_send = "none"
        elif self.paid_online or float_is_zero(
            self.amount_total, precision_rounding=self.currency_id.rounding
        ):
            report_to_send = "invoice_confirmation"
        else:
            report_to_send = "invoice_report"
        res.update(
            {
                "invoicing_method": self.invoicing_method,
                "paid_online": self.paid_online,
                "report_to_send": report_to_send,
            }
        )
        return res

    def _prepare_subscription_data(self, template):
        # Propagates subscription fields values to the subscription
        res = super()._prepare_subscription_data(template)
        res.update(
            {
                "wim_payment_type": self.wim_payment_type,
                "online_renewal": self.online_renewal,
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


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    subscription_id = fields.Many2one(index=True)
