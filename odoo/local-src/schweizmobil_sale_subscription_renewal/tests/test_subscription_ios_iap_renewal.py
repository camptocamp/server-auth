# Copyright 2023 Camptocamp SA
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl)
from odoo.addons.schweizmobil_sale_subscription.tests.test_subscription_ios_iap_renewal import (
    TestSubscriptionIosIapRenewal,
)


class TestSubscriptionIosIapReactivation(TestSubscriptionIosIapRenewal):
    def test_ios_iap_reactivation(self):
        self.sale_order_5.write(
            {
                "online_renewal": "ios_iap",
                "wim_payment_type": "inAppAppleStore",
            }
        )
        self.sale_order_5.action_confirm()
        subscription = self.sale_order_5.order_line.subscription_id
        actual_renewal_date = subscription.next_online_renewal_date
        self.assertEqual(actual_renewal_date, subscription.next_invoicing_date)
        first_invoice = self.sale_order_5._create_invoices()
        first_invoice.action_post()
        self._pay_invoice(first_invoice)
        subscription._recurring_create_invoice()
        recurring_invoice = self.env["account.move"].search(
            [
                ('invoice_line_ids.subscription_id', '=', subscription.id),
                ("id", "!=", first_invoice.id),
            ]
        )
        # Expire the subscription with unpaid recurring invoice
        subscription.set_close()
        self.assertFalse(subscription.in_progress)
        self.assertFalse(subscription.next_online_renewal_date)
        recurring_invoice.button_cancel()
        self.assertEqual(recurring_invoice.state, "cancel")
        # Reactivate the subscription
        renewal_action = subscription.prepare_renewal_order()
        self.assertFalse(subscription.next_online_renewal_date)
        renewal_so = self.env["sale.order"].browse(
            renewal_action.get("res_id")
        )
        renewal_so.action_confirm()
        self.assertEqual(subscription.online_renewal, 'none')
        self.assertEqual(subscription.wim_payment_type, 'inAppAppleStore')
        self.assertFalse(subscription.next_online_renewal_date)
