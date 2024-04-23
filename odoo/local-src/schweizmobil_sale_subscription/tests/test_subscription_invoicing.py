# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from unittest import mock

from dateutil.relativedelta import relativedelta
from freezegun import freeze_time

from odoo import exceptions
from odoo.addons.schweizmobil_sale_subscription.tests.common_subscription_ios_iap import (
    TestSMSubscriptionCommon,
)
from odoo.tests import tagged

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


@tagged('-at_install', 'post_install')
class TestSubscriptionInvoicing(TestSMSubscriptionCommon):
    def test_invoice_from_order(self):
        def test_sub(order, vals, result):
            price_unit = vals.pop("price_unit")
            order.order_line.write({"price_unit": price_unit})
            order.write(vals)
            invoice_vals = order._prepare_invoice()
            self.assertEqual(invoice_vals.get("report_to_send"), result)
            self.assertEqual(invoice_vals.get("paid_online"), vals.get("paid_online"))

        for report_to_send, order_vals in MAPPING_ORDER_VALUES.items():
            for vals in order_vals:
                test_sub(self.subscription, vals, report_to_send)
        for report_to_send, order_vals in MAPPING_ORDER_VALUES_IOS.items():
            for vals in order_vals:
                test_sub(self.subscription_ios_iap, vals, report_to_send)

    def test_invoice_from_subscription_ios_renewal(self):
        self.subscription_ios_iap.action_confirm()
        for report_to_send, order_vals in MAPPING_SUBSCRIPTION_VALUES.items():
            for vals in order_vals:
                self.assertEqual(self.subscription_ios_iap.online_renewal, "ios_iap")

                self.subscription_ios_iap._create_recurring_invoice()
                recurring_invoice = self.env["account.move"].search(
                    [
                        (
                            'invoice_line_ids.subscription_id',
                            '=',
                            self.subscription_ios_iap.id,
                        )
                    ]
                )
                self.assertEqual(recurring_invoice.report_to_send, report_to_send)
                self.assertTrue(recurring_invoice.paid_online)
                recurring_invoice._post()
                # make sure no sftp_pdf_path set on invoice (it gets updated when invoice is pushed to sftp)
                self.assertFalse(recurring_invoice.sftp_pdf_path)

    def test_followup_no_report_to_send(self):
        self.subscription_ios_iap.action_confirm()
        self.subscription.action_confirm()
        for report_to_send, order_vals in MAPPING_SUBSCRIPTION_VALUES.items():
            for vals in order_vals:
                self.subscription_ios_iap.write(vals)
                self.assertEqual(self.subscription_ios_iap.online_renewal, "ios_iap")

                self.subscription_ios_iap._create_recurring_invoice()
                self.subscription_ios_iap._create_recurring_invoice()
                recurring_invoice, recurring_invoice_2 = self.env[
                    "account.move"
                ].search(
                    [
                        (
                            'invoice_line_ids.subscription_id',
                            '=',
                            self.subscription_ios_iap.id,
                        )
                    ]
                )
                self.assertEqual(recurring_invoice.report_to_send, report_to_send)
                self.assertEqual(recurring_invoice_2.report_to_send, report_to_send)
                self.assertTrue(recurring_invoice.paid_online)
                self.assertTrue(recurring_invoice_2.paid_online)
                recurring_invoice.button_draft()
                recurring_invoice._post()
                recurring_invoice_2._post()

                date_overdue = (
                    recurring_invoice.invoice_date_due + relativedelta(days=10)
                ).strftime("%Y-%m-%d")

                with freeze_time(date_overdue):
                    inv_partner = recurring_invoice.partner_id
                    inv_partner._compute_unpaid_invoices()
                    unpaid_invoices = inv_partner.unpaid_invoice_ids
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
        self.subscription_ios_iap.action_confirm()
        for report_to_send, order_vals in MAPPING_SUBSCRIPTION_VALUES.items():
            for vals in order_vals:
                self.subscription_ios_iap.write(vals)
                self.assertEqual(self.subscription_ios_iap.online_renewal, "ios_iap")

                # create 2 unpaid invoices with different type of report to send
                self.subscription_ios_iap._create_recurring_invoice()
                self.subscription_ios_iap._create_recurring_invoice()
                recurring_invoice, recurring_invoice_2 = self.env[
                    "account.move"
                ].search(
                    [
                        (
                            'invoice_line_ids.subscription_id',
                            '=',
                            self.subscription_ios_iap.id,
                        )
                    ]
                )

                recurring_invoice.report_to_send = "invoice_report"
                recurring_invoice.button_draft()
                recurring_invoice._post()

                recurring_invoice_2.report_to_send = "none"
                recurring_invoice_2._post()
                date_overdue = (
                    recurring_invoice.invoice_date_due + relativedelta(days=10)
                ).strftime("%Y-%m-%d")
                with freeze_time(date_overdue):
                    inv_partner = recurring_invoice.partner_id
                    inv_partner._compute_unpaid_invoices()
                    unpaid_invoice = inv_partner.unpaid_invoice_ids
                    self.assertEqual(len(unpaid_invoice), 2)
                    self.assertEqual(unpaid_invoice[1].report_to_send, "invoice_report")
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
        self.subscription.payment_token_id = (self.payment_token.id,)
        self.subscription.action_confirm()
        self.subscription._create_recurring_invoice()
        invoice = self.env["account.move"].search(
            [('invoice_line_ids.subscription_id', '=', self.subscription.id)]
        )
        invoice.action_post()
        self.assertEqual(invoice.payment_state, "not_paid")
        msg = "All related posted invoices should be paid\n%s" % invoice.name
        with self.assertRaisesRegex(
            exceptions.ValidationError,
            msg,
        ):
            self.subscription.write({"online_renewal": "none"})
        invoice.button_draft()
        self.subscription.write({"online_renewal": "none"})

    def test_mixin_constrain(self):
        self.assertEqual(self.subscription.online_renewal, "none")
        with self.assertRaises(exceptions.UserError):
            self.subscription.write({"online_renewal": "ios_iap"})
