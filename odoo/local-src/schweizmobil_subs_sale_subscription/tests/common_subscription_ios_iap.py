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
            "schweizmobil_subs_sale_subscription.product_product_schweizmobil_plus"
        )
        cls.followup_line = cls.env['account_followup.followup.line'].create(
            {
                'name': 'followup delay 1',
                'delay': 1,
                'company_id': cls.company_data['company'].id,
            }
        )
        cls.user_portal.partner_id.followup_line_id = cls.followup_line.id
        cls.subscription_ios_iap = cls.env['sale.order'].create(
            {
                'name': 'TestSO5',
                'sale_order_template_id': cls.env.ref(
                    'schweizmobil_subs_sale_subscription.sale_subscription_template_schweizmobil_plus'
                ).id,
                'partner_id': cls.user_portal.partner_id.id,
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
                "online_renewal": "ios_iap",
                "wim_payment_type": "inAppAppleStore",
                "payment_token_id": cls.payment_token.id,
                "invoicing_method": "",
                "paid_online": True,
            }
        )

    @classmethod
    def _pay_invoice(cls, invoice):
        wiz_action = invoice.action_register_payment()
        wiz = (
            cls.env[wiz_action['res_model']]
            .with_context(wiz_action['context'])
            .create({})
        )
        wiz.action_create_payments()
