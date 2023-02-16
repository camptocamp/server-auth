# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.osv import expression
from odoo.tools import float_is_zero


class SaleSubscription(models.Model):

    _name = "sale.subscription"
    _inherit = ["sale.subscription", "sale.payment.subscription.fields.mixin"]

    first_invoice_id = fields.Many2one(
        "account.move", compute="_compute_first_invoice_id", store=True
    )
    first_invoice_to_be_paid_before = fields.Date(
        compute="_compute_first_invoice_to_be_paid_before",
        store=True,
        help="Limit date after which the first invoice should be paid",
    )
    has_first_invoice_overdue = fields.Boolean(
        compute="_compute_has_first_invoice_overdue",
        search="_search_has_first_invoice_overdue",
    )
    order_line_ids = fields.One2many(
        "sale.order.line", inverse_name="subscription_id"
    )
    invoice_line_ids = fields.One2many(
        "account.move.line", inverse_name="subscription_id"
    )

    customer_number = fields.Char(related="partner_id.customer_number")

    duration = fields.Integer(
        'Total Duration (days)', compute="_compute_duration", store=True
    )
    duration_display = fields.Char(
        'Total Duration', compute="_compute_duration", store=True
    )
    recurring_next_date = fields.Date(tracking=101)

    next_online_renewal_date = fields.Date(
        compute="_compute_next_online_renewal_date", store=True
    )

    @api.depends(
        "in_progress",
        "to_close",
        "online_renewal",
        "next_invoicing_date",
        "invoice_line_ids.move_id.invoice_payment_state",
    )
    def _compute_next_online_renewal_date(self):
        for sub in self:
            next_renewal_date = False
            if (
                sub.online_renewal == "ios_iap"
                and sub.in_progress
                and not sub.to_close
            ):
                has_open_invoice = any(
                    inv.invoice_payment_state == "not_paid"
                    for inv in sub.invoice_line_ids.mapped("move_id")
                )
                if has_open_invoice:
                    continue
                next_renewal_date = sub.next_invoicing_date
            sub.next_online_renewal_date = next_renewal_date

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

    @api.depends(
        "order_line_ids.invoice_lines.move_id",
        "order_line_ids.invoice_lines.move_id.state",
        "order_line_ids.invoice_lines.move_id.type",
    )
    def _compute_first_invoice_id(self):
        for record in self:
            order_line = fields.first(record.order_line_ids)
            if order_line:
                account_move = order_line.invoice_lines.move_id.filtered(
                    lambda move: move.type == 'out_invoice'
                    and move.state == "posted"
                )
                if account_move:
                    record.first_invoice_id = fields.first(account_move)
                    continue
            record.first_invoice_id = False

    @api.depends(
        "first_invoice_id",
        "first_invoice_id.invoice_date_due",
        "closing_delay_type",
        "closing_delay",
    )
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

    def _first_invoice_overdue_domain(self):
        return [
            ("in_progress", "=", True),
            ("first_invoice_id.paid_online", "=", False),
            ("first_invoice_to_be_paid_before", "<=", fields.Date.today()),
            ("first_invoice_id.invoice_payment_state", "=", "not_paid"),
        ]

    @api.depends(
        "in_progress",
        "first_invoice_id.paid_online",
        "first_invoice_to_be_paid_before",
        "first_invoice_id.invoice_payment_state",
    )
    def _compute_has_first_invoice_overdue(self):
        with_invoice_overdue = self.search(
            expression.AND(
                [
                    self._first_invoice_overdue_domain(),
                    [("id", "in", self.ids)],
                ]
            )
        )
        if with_invoice_overdue:
            with_invoice_overdue.has_first_invoice_overdue = True
        without_invoice_overdue_ids = set(self.ids) - set(
            with_invoice_overdue.ids
        )
        if without_invoice_overdue_ids:
            without_invoice_overdue = self.browse(without_invoice_overdue_ids)
            without_invoice_overdue.has_first_invoice_overdue = False

    def _search_has_first_invoice_overdue(self, operator, value):
        # Code inspired by odoo search on is_follower
        with_invoice_overdue = self.search(
            self._first_invoice_overdue_domain()
        )
        # Cases ('has_first_invoice_overdue', '=', True) or ('has_first_invoice_overdue', '!=', False)
        if (operator == '=' and value) or (operator == '!=' and not value):
            return [('id', 'in', with_invoice_overdue.ids)]
        else:
            return [('id', 'not in', with_invoice_overdue.ids)]

    @api.model
    def _cron_close_subscriptions_with_first_invoice_overdue(self):
        subs_to_close = self.search(self._first_invoice_overdue_domain())
        subs_to_close.set_close()

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

    def _prepare_invoice_data(self):
        res = super()._prepare_invoice_data()
        if float_is_zero(
            self.recurring_amount_total,
            precision_rounding=self.currency_id.rounding,
        ):
            report_to_send = "invoice_confirmation"
        else:
            report_to_send = "invoice_report"
        res.update({"report_to_send": report_to_send})
        return res
