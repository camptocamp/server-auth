# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo.addons.schweizmobil_sale_subscription.tests.common_subscription_ios_iap import (
    TestSMSubscriptionCommon,
)


class TestSubscriptionIosIapRenewal(TestSMSubscriptionCommon):
    def test_no_online_renewal_next_online_renewal_date(self):
        self.assertEqual(self.sale_order_5.online_renewal, "none")
        self.sale_order_5.action_confirm()
        subscription = self.sale_order_5.order_line.subscription_id
        self.assertEqual(subscription.online_renewal, "none")
        self.assertFalse(subscription.next_online_renewal_date)

    def test_remove_online_renewal_next_online_renewal_date(self):
        self.sale_order_ios_iap.action_confirm()
        subscription = self.sale_order_ios_iap.order_line.subscription_id
        self.assertEqual(subscription.online_renewal, "ios_iap")
        self.assertEqual(
            subscription.next_online_renewal_date,
            subscription.next_invoicing_date,
        )
        subscription.write({"online_renewal": "none"})
        self.assertFalse(subscription.next_online_renewal_date)

    def test_set_to_close_next_online_renewal_date(self):
        self.sale_order_ios_iap.action_confirm()
        subscription = self.sale_order_ios_iap.order_line.subscription_id
        self.assertEqual(subscription.online_renewal, "ios_iap")
        self.assertEqual(
            subscription.next_online_renewal_date,
            subscription.next_invoicing_date,
        )
        subscription.write({"to_close": True})
        self.assertFalse(subscription.next_online_renewal_date)

    def test_ios_iap_renewal_date(self):
        self.schweizmobil_plus_product.subscription_template_id.payment_mode = (
            "draft_invoice"
        )
        subscription = self._confirm_get_subscription(self.sale_order_ios_iap)
        self.assertEqual(subscription.online_renewal, 'ios_iap')
        self.assertEqual(subscription.wim_payment_type, 'inAppAppleStore')
        actual_renewal_date = subscription.next_online_renewal_date
        self.assertEqual(actual_renewal_date, subscription.next_invoicing_date)
        first_invoice = self.sale_order_ios_iap._create_invoices()
        self.assertEqual(
            subscription.next_online_renewal_date, actual_renewal_date
        )
        first_invoice.action_post()
        self.assertEqual(
            subscription.next_online_renewal_date, actual_renewal_date
        )
        self._pay_invoice(first_invoice)
        self.assertEqual(
            subscription.next_online_renewal_date, actual_renewal_date
        )
        subscription._recurring_create_invoice()
        recurring_invoice = self.env["account.move"].search(
            [
                ('invoice_line_ids.subscription_id', '=', subscription.id),
                ("id", "!=", first_invoice.id),
            ]
        )
        recurring_invoice.action_post()
        self.assertEqual(recurring_invoice.invoice_payment_state, "not_paid")
        self.assertEqual(
            subscription.next_online_renewal_date, actual_renewal_date
        )
        self.assertNotEqual(
            subscription.next_online_renewal_date,
            subscription.next_invoicing_date,
        )
        self._pay_invoice(recurring_invoice)
        self.assertEqual(recurring_invoice.invoice_payment_state, "paid")
        self.assertNotEqual(
            subscription.next_online_renewal_date, actual_renewal_date
        )
        self.assertEqual(
            subscription.next_online_renewal_date,
            subscription.next_invoicing_date,
        )
