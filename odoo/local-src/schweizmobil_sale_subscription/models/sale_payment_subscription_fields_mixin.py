# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import _, api, exceptions, fields, models


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
        selection="_selection_online_renewal",
        default="none",
        help="""This defines if the payment is being renewed online.
        In case of an online renewal, no invoice will be sent to the customer.""",
    )

    def write(self, vals):
        renewal = vals.get("online_renewal")
        forbidden_records = self.filtered(lambda s: s.online_renewal == 'none')
        if renewal and renewal == 'ios_iap' and forbidden_records:
            raise exceptions.UserError(
                _("Update to iOS IAP allowed only from customer device")
            )
        return super().write(vals)
