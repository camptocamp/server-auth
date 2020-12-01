# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import api, fields, models


class SaleSubscription(models.Model):

    _inherit = "sale.subscription"

    first_invoice_id = fields.Many2one(
        "account.move", compute="_compute_first_invoice_id", store=True
    )
    first_invoice_to_be_paid_before = fields.Date(
        compute="_compute_first_invoice_to_be_paid_before",
        store=True,
        help="Limit date after which the first invoice should be paid",
    )
    order_line_ids = fields.One2many(
        "sale.order.line", inverse_name="subscription_id"
    )

    @api.depends("order_line_ids.invoice_lines.move_id")
    def _compute_first_invoice_id(self):
        for record in self:
            order_line = fields.first(record.order_line_ids)
            if order_line:
                account_move = order_line.invoice_lines.move_id.filtered(
                    lambda move: move.type in ('out_invoice', 'out_refund')
                )
                if account_move:
                    record.first_invoice_id = account_move
                    continue
            record.first_invoice_id = False

    @api.depends("first_invoice_id", "first_invoice_id.invoice_date_due")
    def _compute_first_invoice_to_be_paid_before(self):
        for record in self:
            date_due = record.first_invoice_id.invoice_date_due
            if date_due:
                date_due_extended = record._get_recurring_next_date(
                    record.closing_delay_type,
                    record.closing_delay,
                    date_due,
                    date_due.day,
                )
                record.first_invoice_to_be_paid_before = date_due_extended
            else:
                record.first_invoice_to_be_paid_before = False
