# Copyright 2023 Camptocamp SA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl)

from odoo import _, models
from odoo.exceptions import ValidationError


class SaleLoyaltyCouponWizard(models.TransientModel):
    _inherit = 'sale.loyalty.coupon.wizard'

    def action_apply(self):
        if self.order_id.online_renewal == "ios_iap":
            raise ValidationError(
                _(
                    """Discounts are not applicable on order being renewed
                    through iOS IAP. Please change the Online renewal method
                    to apply a discount"""
                )
            )
        return super().action_apply()
