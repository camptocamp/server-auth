# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
from dateutil.relativedelta import relativedelta

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

    customer_number = fields.Char(related="partner_id.customer_number")

    duration = fields.Integer(
        'Total Duration (days)', compute="_compute_duration", store=True
    )
    duration_display = fields.Char(
        'Total Duration', compute="_compute_duration", store=True
    )
    recurring_next_date = fields.Date(tracking=101)

    @api.depends('date_start', 'date')
    def _compute_duration(self):
        for rec in self:
            if not (rec.date and rec.date_start):
                days = 0
                duration_display = '0'
            else:
                days = (rec.date - rec.date_start).days
                delta = relativedelta(rec.date, rec.date_start)
                parts = []
                if delta.years:
                    parts.append(
                        '%d year%s'
                        % (delta.years, 's' if delta.years > 1 else '')
                    )
                if delta.months:
                    parts.append(
                        '%d month%s'
                        % (delta.months, 's' if delta.months > 1 else '')
                    )
                if delta.days:
                    parts.append(
                        '%d day%s'
                        % (delta.days, 's' if delta.days > 1 else '')
                    )
                duration_display = "% 5d days (" % days + " ".join(parts) + ")"
            rec.duration = days
            rec.duration_display = duration_display

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

    def validate_and_send_invoice(self, invoice):
        """actually don't send the invoice by email unless
        context['send_invoice_by_email'] is True. Otherwise, post the invoice
        and request a queue job to generate the PDF
        """
        if self.env.context.get('send_invoice_by_email', False):
            return super().validate_and_send_invoice()
        self.ensure_one()
        invoice.post()
        return True
