# Copyright 2023 Camptocamp SA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl)

from odoo import _, models


class SaleCouponApplyCode(models.TransientModel):
    _inherit = "sale.subscription.apply.code"

    def apply_code(self):
        if self.subscription_id.online_renewal == "ios_iap":
            return {
                'error': _(
                    """Discounts are not applicable on subscription being renewed
                    through iOS IAP. Please change the Online renewal method
                    to apply a discount"""
                )
            }
        return super().apply_code()
