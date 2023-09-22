# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from dateutil.relativedelta import relativedelta

import mock
from freezegun import freeze_time
from odoo import exceptions
from odoo.addons.schweizmobil_sale_subscription.tests.common_subscription_ios_iap import (
    TestSMSubscriptionCommon,
)

MAPPING_ORDER_VALUES = {
    "invoice_confirmation": [
        {"online_renewal": "none", "paid_online": True, "price_unit": 12.0},
        {"online_renewal": "none", "paid_online": False, "price_unit": 0.0},
    ],
    "invoice_report": [
        {"online_renewal": "none", "paid_online": False, "price_unit": 12.0}
    ],
}
MAPPING_ORDER_VALUES_IOS = {"none": [{"paid_online": True, "price_unit": 0.0}]}

MAPPING_SUBSCRIPTION_LINE_VALUES = {
    "invoice_confirmation": [{"price_unit": 0.0}],
    "invoice_report": [{"price_unit": 42.0}],
}

MAPPING_SUBSCRIPTION_VALUES = {
    "none": [
        {
            # ios type can be set only on the moment of creation
            # "online_renewal": "ios_iap"
        }
    ]
}


RESULTS = {
    "invoice_35": {
        "from_so": {"invoice": "invoice_report", "followup": "invoice_report"},
        "from_sub": {
            "invoice": "invoice_report",
            "followup": "invoice_report",
        },
    },
    "invoice_0": {
        "from_so": {"invoice": "invoice_confirmation", "followup": False},
        "from_sub": {"invoice": "invoice_confirmation", "followup": False},
    },
    "ios_iap": {
        "from_so": {"invoice": "invoice_confirmation", "followup": False},
        "from_sub": {
            "invoice": "invoice_report",
            "followup": "invoice_report",
        },
    },
}


class TestSubscriptionInvoicing(TestSMSubscriptionCommon):
    def test_invoice_from_order(self):
        def test_sub(order, vals, result):
            price_unit = vals.pop("price_unit")
            order.order_line.write({"price_unit": price_unit})
            order.write(vals)
            invoice_vals = order._prepare_invoice()
            self.assertEqual(invoice_vals.get("report_to_send"), result)
            self.assertEqual(
                invoice_vals.get("paid_online"), vals.get("paid_online")
            )

        for report_to_send, order_vals in MAPPING_ORDER_VALUES.items():
            for vals in order_vals:
                test_sub(self.sale_order, vals, report_to_send)

        for report_to_send, order_vals in MAPPING_ORDER_VALUES_IOS.items():
            for vals in order_vals:
                test_sub(self.sale_order_ios_iap, vals, report_to_send)

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
        self.schweizmobil_plus_product.subscription_template_id.payment_mode = (
            "draft_invoice"
        )
        subscription_ios = self._confirm_get_subscription(
            self.sale_order_ios_iap
        )
        for report_to_send, order_vals in MAPPING_SUBSCRIPTION_VALUES.items():
            for vals in order_vals:
                self.assertEqual(subscription_ios.online_renewal, "ios_iap")

                subscription_ios._recurring_create_invoice()
                recurring_invoice = self.env["account.move"].search(
                    [
                        (
                            'invoice_line_ids.subscription_id',
                            '=',
                            subscription_ios.id,
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
        self.schweizmobil_plus_product.subscription_template_id.payment_mode = (
            "draft_invoice"
        )
        subscription_ios = self._confirm_get_subscription(
            self.sale_order_ios_iap
        )
        for report_to_send, order_vals in MAPPING_SUBSCRIPTION_VALUES.items():
            for vals in order_vals:
                subscription_ios.write(vals)
                self.assertEqual(subscription_ios.online_renewal, "ios_iap")

                # create 2 unpaid invoices
                subscription_ios._recurring_create_invoice()
                subscription_ios._recurring_create_invoice()
                recurring_invoice, recurring_invoice_2 = self.env[
                    "account.move"
                ].search(
                    [
                        (
                            'invoice_line_ids.subscription_id',
                            '=',
                            subscription_ios.id,
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
        self.schweizmobil_plus_product.subscription_template_id.payment_mode = (
            "draft_invoice"
        )
        subscription_ios = self._confirm_get_subscription(
            self.sale_order_ios_iap
        )
        for report_to_send, order_vals in MAPPING_SUBSCRIPTION_VALUES.items():
            for vals in order_vals:
                subscription_ios.write(vals)
                self.assertEqual(subscription_ios.online_renewal, "ios_iap")

                # create 2 unpaid invoices with different type of report to send
                subscription_ios._recurring_create_invoice()
                subscription_ios._recurring_create_invoice()
                recurring_invoice, recurring_invoice_2 = self.env[
                    "account.move"
                ].search(
                    [
                        (
                            'invoice_line_ids.subscription_id',
                            '=',
                            subscription_ios.id,
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

    def test_subscription_constrain(self):
        self.sale_order.action_confirm()
        self.subscription._recurring_create_invoice()
        invoice = self.env["account.move"].search(
            [('invoice_line_ids.subscription_id', '=', self.subscription.id)]
        )
        invoice.action_post()
        self.assertEquals(invoice.invoice_payment_state, "not_paid")
        with self.assertRaisesRegex(
            exceptions.ValidationError,
            r"All related posted invoices should be paid.",
        ):
            self.subscription.write({"online_renewal": "none"})
        invoice.button_draft()
        self.subscription.write({"online_renewal": "none"})

    def test_order_constrain(self):
        self.sale_order.action_confirm()
        self.sale_order.order_line.write({"price_unit": 42.0})
        invoice = self.sale_order._create_invoices()
        invoice.action_post()
        self.assertEquals(invoice.invoice_payment_state, "not_paid")
        with self.assertRaisesRegex(
            exceptions.ValidationError,
            r"All related posted invoices should be paid.",
        ):
            self.sale_order.write({"online_renewal": "none"})
        invoice.button_draft()
        self.sale_order.write({"online_renewal": "none"})

    def test_mixin_constrain(self):
        self.assertEqual(self.sale_order.online_renewal, "none")
        with self.assertRaises(exceptions.UserError):
            self.sale_order.write({"online_renewal": "ios_iap"})
