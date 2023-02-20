# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)

from odoo import _, models


class SaleCouponApplyCode(models.TransientModel):
    _inherit = 'sale.coupon.apply.code'

    def apply_coupon(self, order, coupon_code):

        if order.online_renewal == "ios_iap":
            return {
                'error': _(
                    """Discounts are not applicable on order being renewed
                    through iOS IAP. Please change the Online renewal method
                    to apply a discount"""
                )
            }
        return super().apply_coupon(order, coupon_code)
