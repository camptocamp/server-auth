# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import api, fields, models

PAYMENT_TYPE_MAPPING = [
    ("invoice", "Invoice"),
    ("emailInvoice", "Email Invoice"),
    ("epayment", "E-Payment"),
    ("ebill", "E-Bill"),
    ("inAppAppleStore", "In Apple Store"),
]
ONLINE_RENEWAL_MAPPING = [("none", "None"), ("iOS IAP", "iOS IAP")]


class SalePaymentSubscriptionFieldsMixin(models.AbstractModel):

    _name = "sale.payment.subscription.fields.mixin"
    _description = "Payment fields for sale process"

    @api.model
    def _get_wim_payment_type_selection(self):
        return PAYMENT_TYPE_MAPPING

    @api.model
    def _get_online_renewal_selection(self):
        return ONLINE_RENEWAL_MAPPING

    wim_payment_type = fields.Selection(
        selection="_get_wim_payment_type_selection", readonly=True
    )
    online_renewal = fields.Selection(
        selection="_get_online_renewal_selection",
        default="none",
        readonly=True,
    )
