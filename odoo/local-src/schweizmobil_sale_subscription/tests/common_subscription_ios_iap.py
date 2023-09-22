# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo.addons.sale_subscription.tests.common_sale_subscription import (
    TestSubscriptionCommon,
)


class TestSMSubscriptionCommon(TestSubscriptionCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.schweizmobil_plus_product = cls.env.ref(
            "schweizmobil_sale_subscription.product_product_schweizmobil_plus"
        )
        cls.sale_order_ios_iap = cls._create_sale_order(
            cls.user_portal.partner_id,
            "inAppAppleStore",
            "ios_iap",
            paid_online=True,
        )

    @classmethod
    def _create_sale_order(
        cls,
        partner,
        wim_payment_type,
        online_renewal,
        invoicing_method="",
        paid_online=False,
    ):
        return cls.env["sale.order"].create(
            {
                'name': 'TestSO5',
                'partner_id': partner.id,
                'order_line': [
                    (
                        0,
                        0,
                        {
                            'name': cls.schweizmobil_plus_product.name,
                            'product_id': cls.schweizmobil_plus_product.id,
                            'product_uom_qty': 1.0,
                            'product_uom': cls.schweizmobil_plus_product.uom_id.id,
                            'price_unit': cls.schweizmobil_plus_product.list_price,
                        },
                    )
                ],
                "online_renewal": online_renewal,
                "wim_payment_type": wim_payment_type,
                "invoicing_method": invoicing_method,
                "paid_online": paid_online,
            }
        )

    @classmethod
    def _confirm_get_subscription(self, sale_order):
        sale_order.action_confirm()
        return sale_order.order_line.subscription_id

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
