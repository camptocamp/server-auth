# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo.addons.schweizmobil_sale_subscription.tests.common_subscription_ios_iap import (
    TestSMSubscriptionCommon,
)
from odoo.tests import tagged


@tagged('-at_install', 'post_install')
class TestSubscriptionIosIapRenewal(TestSMSubscriptionCommon):
    def test_remove_online_renewal_next_online_renewal_date(self):
        self.subscription_ios_iap.action_confirm()
        self.assertEqual(self.subscription_ios_iap.online_renewal, "ios_iap")
        self.assertEqual(
            self.subscription_ios_iap.next_online_renewal_date,
            self.subscription_ios_iap.next_invoicing_date,
        )
        self.subscription_ios_iap.write({"online_renewal": "none"})
        self.assertFalse(self.subscription_ios_iap.next_online_renewal_date)

    def test_set_to_close_next_online_renewal_date(self):
        self.subscription_ios_iap.action_confirm()
        self.assertEqual(self.subscription_ios_iap.online_renewal, "ios_iap")
        self.assertEqual(
            self.subscription_ios_iap.next_online_renewal_date,
            self.subscription_ios_iap.next_invoicing_date,
        )
        self.subscription_ios_iap.sale_order_template_id.is_unlimited = False
        self.subscription_ios_iap.write({"to_close": True})
        self.assertFalse(self.subscription_ios_iap.next_online_renewal_date)

    def test_ios_iap_renewal_date(self):
        self.subscription_ios_iap.action_confirm()
        subscription = self.subscription_ios_iap
        self.assertEqual(subscription.online_renewal, 'ios_iap')
        self.assertEqual(subscription.wim_payment_type, 'inAppAppleStore')
        actual_renewal_date = subscription.next_online_renewal_date
        self.assertEqual(actual_renewal_date, subscription.next_invoicing_date)
        subscription._create_recurring_invoice()
        self.assertEqual(subscription.next_online_renewal_date, actual_renewal_date)
        recurring_invoice = self.env["account.move"].search(
            [
                ('invoice_line_ids.subscription_id', '=', subscription.id),
            ]
        )
        recurring_invoice._post()
        self.assertEqual(subscription.next_online_renewal_date, actual_renewal_date)
        self._pay_invoice(recurring_invoice)
        self.assertEqual(recurring_invoice.payment_state, "in_payment")
        self.assertNotEqual(subscription.next_online_renewal_date, actual_renewal_date)
