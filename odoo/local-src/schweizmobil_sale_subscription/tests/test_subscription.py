# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

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

MAPPING_SUBSCRIPTION_VALUES = {
    "invoice_confirmation": [{"price_unit": 0.0}],
    "invoice_report": [{"price_unit": 42.0}],
}


class TestSubscription(TestSubscriptionCommon):
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

    def test_invoice_from_subscription(self):
        self.sale_order.action_confirm()
        for report_to_send, order_vals in MAPPING_SUBSCRIPTION_VALUES.items():
            for vals in order_vals:
                self.subscription.recurring_invoice_line_ids.write(vals)
                invoice_vals = self.subscription._prepare_invoice_data()
                self.assertEqual(
                    invoice_vals.get("report_to_send"), report_to_send
                )
