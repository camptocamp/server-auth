# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo.addons.sale_subscription.tests.common_sale_subscription import (
    TestSubscriptionCommon,
)


class TestSubscriptionIosIapRenewalCommon(TestSubscriptionCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.sale_order_ios_iap = cls.env["sale.order"].create(
            {
                'name': 'TestSO5',
                'partner_id': cls.user_portal.partner_id.id,
                'order_line': [
                    (
                        0,
                        0,
                        {
                            'name': cls.product4.name,
                            'product_id': cls.product4.id,
                            'product_uom_qty': 1.0,
                            'product_uom': cls.product4.uom_id.id,
                            'price_unit': cls.product4.list_price,
                        },
                    )
                ],
                "online_renewal": "ios_iap",
                "wim_payment_type": "inAppAppleStore",
            }
        )
        cls.subscription_ios = cls.env["sale.subscription"].browse(
            cls.sale_order_ios_iap.create_subscriptions()
        )

    @classmethod
    def _pay_invoice(cls, invoice):
        payment_method = cls.env["account.payment.method"].search(
            [("code", "=", "manual"), ("payment_type", "=", "inbound")]
        )
        bank_journal = cls.env["account.journal"].search(
            [("type", "=", "bank")], limit=1
        )
        wiz_action = invoice.action_invoice_register_payment()
        payment_wiz = (
            cls.env[wiz_action["res_model"]]
            .with_context(wiz_action["context"])
            .create(
                {
                    "journal_id": bank_journal.id,
                    "payment_method_id": payment_method.id,
                }
            )
        )
        payment_wiz.post()
