# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import api, fields, models


class SalePaymentSubscriptionFieldsMixin(models.AbstractModel):

    _name = "sale.payment.subscription.fields.mixin"
    _description = "Payment fields for sale process"

    @api.model
    def _selection_wim_payment_type(self):
        return [
            ("invoice", "Invoice"),
            ("emailInvoice", "Email Invoice"),
            ("epayment", "E-Payment"),
            ("ebill", "E-Bill"),
            ("inAppAppleStore", "iOS IAP"),
        ]

    @api.model
    def _selection_online_renewal(self):
        return [("none", "None"), ("ios_iap", "iOS IAP")]

    wim_payment_type = fields.Selection(
        selection="_selection_wim_payment_type", readonly=True
    )
    online_renewal = fields.Selection(
        selection="_selection_online_renewal", default="none", readonly=True
    )
