# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from dateutil.relativedelta import relativedelta

import mock
from freezegun import freeze_time
from odoo.addons.sale_subscription.tests.common_sale_subscription import (
    TestSubscriptionCommon,
)

MAPPING_ORDER_VALUES = {
    "invoice_confirmation": [
        {"online_renewal": "none", "paid_online": True, "price_unit": 12.0},
        {"online_renewal": "none", "paid_online": False, "price_unit": 0.0},
    ],
    "invoice_report": [
        {"online_renewal": "none", "paid_online": False, "price_unit": 12.0}
    ],
    "none": [
        {"online_renewal": "ios_iap", "paid_online": True, "price_unit": 0.0}
    ],
}

MAPPING_SUBSCRIPTION_LINE_VALUES = {
    "invoice_confirmation": [{"price_unit": 0.0}],
    "invoice_report": [{"price_unit": 42.0}],
}

MAPPING_SUBSCRIPTION_VALUES = {"none": [{"online_renewal": "ios_iap"}]}


class TestSubscriptionInvoicing(TestSubscriptionCommon):
    def test_invoice_from_order(self):
        for report_to_send, order_vals in MAPPING_ORDER_VALUES.items():
            for vals in order_vals:
                price_unit = vals.pop("price_unit")
                self.sale_order.order_line.write({"price_unit": price_unit})
                self.sale_order.write(vals)
                invoice_vals = self.sale_order._prepare_invoice()
                self.assertEqual(
                    invoice_vals.get("report_to_send"), report_to_send
                )
                self.assertEqual(
                    invoice_vals.get("paid_online"), vals.get("paid_online")
                )

    def test_invoice_from_subscription(self):
        self.sale_order.action_confirm()
        for (
            report_to_send,
            order_vals,
        ) in MAPPING_SUBSCRIPTION_LINE_VALUES.items():
            for vals in order_vals:
                self.subscription.recurring_invoice_line_ids.write(vals)
                invoice_vals = self.subscription._prepare_invoice_data()
                self.assertEqual(
                    invoice_vals.get("report_to_send"), report_to_send
                )

    def test_invoice_from_subscription_ios_renewal(self):
        self.sale_order.action_confirm()
        for report_to_send, order_vals in MAPPING_SUBSCRIPTION_VALUES.items():
            for vals in order_vals:
                self.subscription.write(vals)
                self.assertEqual(self.subscription.online_renewal, "ios_iap")

                self.subscription._recurring_create_invoice()
                recurring_invoice = self.env["account.move"].search(
                    [
                        (
                            'invoice_line_ids.subscription_id',
                            '=',
                            self.subscription.id,
                        )
                    ]
                )
                self.assertEqual(
                    recurring_invoice.report_to_send, report_to_send
                )
                self.assertFalse(recurring_invoice.paid_online)
                recurring_invoice.with_context(
                    test_queue_job_no_delay=True
                ).post()
                # make sure no sftp_pdf_path set on invoice (it gets updated when invoice is pushed to sftp)
                self.assertFalse(recurring_invoice.sftp_pdf_path)

    def test_followup_no_report_to_send(self):

        self.sale_order.action_confirm()
        for report_to_send, order_vals in MAPPING_SUBSCRIPTION_VALUES.items():
            for vals in order_vals:
                self.subscription.write(vals)
                self.assertEqual(self.subscription.online_renewal, "ios_iap")

                # create 2 unpaid invoices
                self.subscription._recurring_create_invoice()
                self.subscription._recurring_create_invoice()
                recurring_invoice, recurring_invoice_2 = self.env[
                    "account.move"
                ].search(
                    [
                        (
                            'invoice_line_ids.subscription_id',
                            '=',
                            self.subscription.id,
                        )
                    ]
                )
                self.assertEqual(
                    recurring_invoice.report_to_send, report_to_send
                )
                self.assertEqual(
                    recurring_invoice_2.report_to_send, report_to_send
                )
                self.assertFalse(recurring_invoice.paid_online)
                self.assertFalse(recurring_invoice_2.paid_online)

                recurring_invoice.post()
                recurring_invoice_2.post()

                date_overdue = (
                    recurring_invoice.invoice_date_due + relativedelta(days=10)
                ).strftime("%Y-%m-%d")

                with freeze_time(date_overdue):
                    inv_partner = recurring_invoice.partner_id
                    inv_partner._compute_unpaid_invoices()
                    unpaid_invoices = inv_partner.unpaid_invoices
                    self.assertEqual(len(unpaid_invoices), 2)
                    self.assertEqual(unpaid_invoices[0].report_to_send, "none")
                    self.assertEqual(unpaid_invoices[1].report_to_send, "none")
                    with mock.patch.object(
                        type(self.env['res.partner']), '_generate_followup_pdf'
                    ) as mocked_function:
                        inv_partner.with_context(
                            test_queue_job_no_delay=True
                        )._cron_execute_followup_print_letters()
                        mocked_function.assert_not_called()

    def test_followup_invoice_report_to_send(self):
        self.sale_order.action_confirm()
        for report_to_send, order_vals in MAPPING_SUBSCRIPTION_VALUES.items():
            for vals in order_vals:
                self.subscription.write(vals)
                self.assertEqual(self.subscription.online_renewal, "ios_iap")

                # create 2 unpaid invoices with different type of report to send
                self.subscription._recurring_create_invoice()
                self.subscription._recurring_create_invoice()
                recurring_invoice, recurring_invoice_2 = self.env[
                    "account.move"
                ].search(
                    [
                        (
                            'invoice_line_ids.subscription_id',
                            '=',
                            self.subscription.id,
                        )
                    ]
                )

                recurring_invoice.report_to_send = "invoice_report"
                recurring_invoice.post()

                recurring_invoice_2.report_to_send = "none"
                recurring_invoice_2.post()

                date_overdue = (
                    recurring_invoice.invoice_date_due + relativedelta(days=10)
                ).strftime("%Y-%m-%d")
                with freeze_time(date_overdue):
                    inv_partner = recurring_invoice.partner_id
                    inv_partner._compute_unpaid_invoices()
                    unpaid_invoice = inv_partner.unpaid_invoices
                    self.assertEqual(len(unpaid_invoice), 2)
                    self.assertEqual(
                        unpaid_invoice[1].report_to_send, "invoice_report"
                    )
                    self.assertEqual(unpaid_invoice[0].report_to_send, "none")
                    with mock.patch.object(
                        type(self.env['res.partner']), '_generate_followup_pdf'
                    ) as mocked_function:
                        inv_partner.with_context(
                            test_queue_job_no_delay=True
                        )._cron_execute_followup_print_letters()
                        # make sure it got called only for one invoice
                        mocked_function.assert_called_once()
