# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.addons.sale_subscription.models.sale_order import SUBSCRIPTION_PROGRESS_STATE
from odoo.addons.stock.models.product import OPERATORS
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression
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
    first_invoice_id = fields.Many2one(
        "account.move",
        compute="_compute_first_invoice_id",
        store=True,
        index=True,
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
        "subscription_state",
        "to_close",
        "online_renewal",
        "next_invoicing_date",
        "invoice_ids.payment_state",
    )
    def _compute_next_online_renewal_date(self):
        for sub in self:
            next_renewal_date = False
            if (
                sub.online_renewal == "ios_iap"
                and sub.subscription_state in SUBSCRIPTION_PROGRESS_STATE
                and not sub.to_close
            ):
                has_open_invoice = any(
                    inv.payment_state == "not_paid" for inv in sub.invoice_ids
                )
                if has_open_invoice:
                    continue
                next_renewal_date = sub.next_invoicing_date
            sub.next_online_renewal_date = next_renewal_date

    @api.constrains("online_renewal")
    def _check_payment_status(self):
        for rec in self:
            unpaid_inv = rec.invoice_ids.filtered(
                lambda i: i.payment_state in ("not_paid", "partially")
                and i.state == "posted"
            )

            if unpaid_inv:
                raise ValidationError(
                    _(
                        "All related posted invoices should be paid\n%s"
                        % ", ".join(unpaid_inv.mapped("name"))
                    )
                )

    @api.depends('start_date', 'end_date')
    def _compute_duration(self):
        for rec in self:
            if not (rec.end_date and rec.start_date):
                days = 0
                duration_display = '0'
            else:
                days = (rec.end_date - rec.start_date).days
                delta = relativedelta(rec.end_date, rec.start_date)
                parts = []
                if delta.years:
                    parts.append(
                        '%d year%s' % (delta.years, 's' if delta.years > 1 else '')
                    )
                if delta.months:
                    parts.append(
                        '%d month%s' % (delta.months, 's' if delta.months > 1 else '')
                    )
                if delta.days:
                    parts.append(
                        '%d day%s' % (delta.days, 's' if delta.days > 1 else '')
                    )
                duration_display = "% 5d days (" % days + " ".join(parts) + ")"
            rec.duration = days
            rec.duration_display = duration_display

    @api.depends(
        "invoice_ids",
        "invoice_ids.state",
        "invoice_ids.move_type",
    )
    def _compute_first_invoice_id(self):
        for record in self:
            account_move = record.invoice_ids.filtered(
                lambda move: move.move_type == 'out_invoice' and move.state == "posted"
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
            record.first_invoice_to_be_paid_before = False
            if record.closing_delay_type and record.closing_delay:
                date_due = record.first_invoice_id.invoice_date_due
                if date_due:
                    date_due_extended = record._get_recurring_next_date(
                        record.closing_delay_type,
                        record.closing_delay,
                        date_due,
                        date_due.day,
                    )
                    if date_due_extended:
                        record.first_invoice_to_be_paid_before = date_due_extended

    def _first_invoice_overdue_domain(self):
        return [
            ("subscription_state", "in", SUBSCRIPTION_PROGRESS_STATE),
            ("first_invoice_id.paid_online", "=", False),
            ("first_invoice_to_be_paid_before", "<=", fields.Date.today()),
            ("first_invoice_id.payment_state", "=", "not_paid"),
        ]

    @api.depends(
        "subscription_state",
        "first_invoice_id.paid_online",
        "first_invoice_to_be_paid_before",
        "first_invoice_id.payment_state",
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
        without_invoice_overdue_ids = set(self.ids) - set(with_invoice_overdue.ids)
        if without_invoice_overdue_ids:
            without_invoice_overdue = self.browse(without_invoice_overdue_ids)
            without_invoice_overdue.has_first_invoice_overdue = False

    def _search_has_first_invoice_overdue(self, operator, value):
        # Code inspired by odoo search on is_follower
        with_invoice_overdue = self.search(self._first_invoice_overdue_domain())
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
        invoice._post()
        return True

    def _prepare_invoice(self):
        res = super()._prepare_invoice()
        if self.online_renewal == "ios_iap":
            report_to_send = "none"
        elif self.paid_online or float_is_zero(
            self.amount_to_invoice,
            precision_rounding=self.currency_id.rounding,
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

    def _prepare_upsell_renew_order_values(self, subscription_state):
        # Propagates subscription fields values to the subscription
        res = super()._prepare_upsell_renew_order_values(subscription_state)
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
        self.flush_model(["order_line"])
        self.env["sale.order.line"].flush_model(["invoice_lines"])
        self.env["account.move.line"].flush_model(["move_id"])
        self.env["account.move"].flush_model(["move_type"])
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
        res = [tpl[0] for tpl in query_res if OPERATORS[operator](tpl[1], value)]
        return [('id', 'in', res)]


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    analytic_account_id = fields.Many2one('account.analytic.account', index=True)
