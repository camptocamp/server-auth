# Copyright 2023 Camptocamp SA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl)

from odoo.addons.sale_subscription.tests.common_sale_subscription import (
    TestSubscriptionCommon,
)
from odoo.tests import SavepointCase


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
        cls.program = cls.env["sale.coupon.program"].create(
            {
                "name": "Test program",
                "promo_code_usage": "code_needed",
                "discount_line_product_id": cls.discount_product.id,
                "promo_code": cls.coupon_code,
                "discount_type": "fixed_amount",
                "promo_applicability": "on_current_order",
                "discount_fixed_amount": 10,
            }
        )
        cls.discount_product.product_tmpl_id.write(
            {
                "recurring_invoice": True,
                "subscription_template_id": cls.subscription_tmpl.id,
            }
        )
        cls.wizard_obj = cls.env["sale.subscription.apply.code"]
        cls.subscription = cls.env['sale.subscription'].create(
            {
                'name': 'TestSubscription',
                'partner_id': cls.user_portal.partner_id.id,
                'pricelist_id': cls.env.ref('product.list0').id,
                'template_id': cls.subscription_tmpl.id,
                'online_renewal': 'ios_iap',
                "recurring_invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": cls.product.id,
                            "price_unit": 100,
                            "quantity": 1,
                            "uom_id": cls.product.uom_id.id,
                        },
                    )
                ],
            }
        )

    def test_subscription_ios_iap(self):
        self.assertFalse(self.program.subscription_count)
        wizard = self.wizard_obj.create(
            {"coupon_code": "ios_iap", "subscription_id": self.subscription.id}
        )
        res = wizard.apply_code()
        self.assertEqual(
            res,
            {
                "error": """Discounts are not applicable on subscription being renewed
                    through iOS IAP. Please change the Online renewal method
                    to apply a discount"""
            },
        )
        self.subscription.write({'online_renewal': 'none'})
        res = wizard.apply_code()
        self.program._compute_subscription_count()
        self.assertEqual(self.program.subscription_count, 1)


class TestSaleWizard(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(
            context=dict(
                cls.env.context,
                tracking_disable=True,
                test_partner_mismatch=True,
            )
        )
        cls.order = cls.env['sale.order'].create(
            {
                'partner_id': cls.env.ref("base.res_partner_2").id,
                'online_renewal': 'ios_iap',
                'order_line': [
                    (
                        0,
                        0,
                        {
                            'product_id': cls.env.ref(
                                'product.product_product_6'
                            ).id,
                            'name': 'Large Cabinet',
                            'product_uom_qty': 4.0,
                        },
                    )
                ],
            }
        )
        cls.program = cls.env['sale.coupon.program'].create(
            {
                'name': 'Code for 10% on orders',
                'promo_code_usage': 'code_needed',
                'promo_code': 'ios_iap',
                'discount_type': 'percentage',
                'discount_percentage': 10.0,
                'program_type': 'promotion_program',
            }
        )

        cls.wizard = cls.env["sale.coupon.apply.code"]

    def test_sale_ios_iap(self):
        # self.program._compute_subscription_count()
        self.assertFalse(self.program.subscription_count)
        self.assertEqual(len(self.order.order_line.ids), 1)
        res = self.wizard.apply_coupon(self.order, "ios_iap")
        self.assertEqual(
            res,
            {
                "error": """Discounts are not applicable on order being renewed
                    through iOS IAP. Please change the Online renewal method
                    to apply a discount"""
            },
        )
        self.assertEqual(len(self.order.order_line.ids), 1)
        self.order.write({'online_renewal': 'none'})
        res = self.wizard.apply_coupon(self.order, "ios_iap")
        self.assertEqual(len(self.order.order_line.ids), 2)
