# Copyright 2023 Camptocamp SA
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl)
from odoo.addons.sale_subscription.models.sale_order import SUBSCRIPTION_PROGRESS_STATE
from odoo.addons.schweizmobil_subs_sale_subscription.tests.common_subscription_ios_iap import (
    TestSMSubscriptionCommon,
)
from odoo.tests import tagged


@tagged('-at_install', 'post_install')
class TestSubscriptionIosIapReactivation(TestSMSubscriptionCommon):
    def test_ios_iap_reactivation(self):
        subscription = self.subscription_ios_iap
        self.subscription_ios_iap.action_confirm()
        actual_renewal_date = subscription.next_online_renewal_date
        self.assertEqual(actual_renewal_date, subscription.next_invoicing_date)
        subscription._create_recurring_invoice()
        recurring_invoice = self.env["account.move"].search(
            [
                ('invoice_line_ids.subscription_id', '=', subscription.id),
            ]
        )
        recurring_invoice._post()
        self._pay_invoice(recurring_invoice)
        # Expire the subscription with unpaid recurring invoice
        subscription.set_close()
        self.assertNotIn(subscription.subscription_state, SUBSCRIPTION_PROGRESS_STATE)
        self.assertFalse(subscription.next_online_renewal_date)
        recurring_invoice.button_cancel()
        self.assertEqual(recurring_invoice.state, "cancel")
        # Reactivate the subscription
        renewal_action = subscription.prepare_renewal_order()
        self.assertFalse(subscription.next_online_renewal_date)
        renewal_sub = self.env["sale.order"].browse(renewal_action.get("res_id"))
        renewal_sub.action_confirm()
        self.assertEqual(renewal_sub.online_renewal, 'none')
        self.assertEqual(renewal_sub.wim_payment_type, 'inAppAppleStore')
        self.assertFalse(renewal_sub.next_online_renewal_date)
