# Copyright 2023 Camptocamp SA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl)

from odoo.addons.sale_subscription.tests.common_sale_subscription import (
    TestSubscriptionCommon,
)
from odoo.exceptions import ValidationError
from odoo.tests import tagged


@tagged('-at_install', 'post_install')
class TestSubscriptionWizard(TestSubscriptionCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.discount_product = cls.env["product.product"].create(
            {
                "name": "Discount Product",
                "type": "service",
                "invoice_policy": "order",
                "list_price": 0.00,
                "sale_ok": False,
            }
        )
        cls.coupon_code = "ios_iap"
        cls.program = cls.env["loyalty.program"].create(
            {
                "name": "Test program",
                "program_type": "promo_code",
                "applies_on": "current",
                "trigger": "with_code",
            }
        )
        cls.rule = cls.env['loyalty.rule'].create(
            {"mode": "with_code", "code": cls.coupon_code, "program_id": cls.program.id}
        )

        cls.reward = cls.env['loyalty.reward'].create(
            {
                "program_id": cls.program.id,
                "reward_type": "discount",
                "discount_mode": "per_point",
                "discount": 10,
                "discount_applicability": "order",
            }
        )
        cls.discount_product.product_tmpl_id.write(
            {
                "recurring_invoice": True,
            }
        )
        cls.coupon_wizard = cls.env["sale.loyalty.coupon.wizard"]
        cls.subscription = cls.env['sale.order'].create(
            {
                'name': 'TestSubscription',
                'partner_id': cls.user_portal.partner_id.id,
                'sale_order_template_id': cls.subscription_tmpl.id,
                'online_renewal': 'ios_iap',
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": cls.product.id,
                            "price_unit": 100,
                            "product_uom_qty": 1,
                            "product_uom": cls.product.uom_id.id,
                        },
                    )
                ],
            }
        )

    def test_subscription_ios_iap(self):
        self.assertFalse(self.program.order_count)
        self.assertEqual(len(self.subscription.order_line.ids), 1)
        wizard = self.coupon_wizard.create(
            {"coupon_code": "ios_iap", "order_id": self.subscription.id}
        )
        with self.assertRaises(ValidationError):
            res = wizard.action_apply()

        self.subscription.write({'online_renewal': 'none'})
        res = wizard.action_apply()
        self.assertEqual(res.get('res_model'), 'sale.loyalty.reward.wizard')
        selected_reward_id = res.get('context').get('default_reward_ids')[0]
        claim_reward_wizard = self.env[res.get('res_model')].create(
            {
                'order_id': self.subscription.id,
                'selected_reward_id': selected_reward_id,
            }
        )
        claim_reward_wizard.action_apply()
        self.assertEqual(self.program.order_count, 1)
        self.assertEqual(len(self.subscription.order_line.ids), 2)
