# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import _, api, exceptions, fields, models

INVOICING_METHOD_MAPPING = [
    ("email", "Email"),
    ("post", "Post"),
    ("ebill", "E-Bill"),
]


class WimPaymentFieldsMixin(models.AbstractModel):

    _name = "wim.payment.fields.mixin"

    @api.model
    def _get_invoicing_method_selection(self):
        return INVOICING_METHOD_MAPPING

    invoicing_method = fields.Selection(
        selection="_get_invoicing_method_selection", readonly=True
    )
    paid_online = fields.Boolean(readonly=True)

    @api.constrains("invoicing_method", "paid_online")
    def _check_paid_online(self):
        for record in self:
            if record.paid_online and record.invoicing_method:
                raise exceptions.ValidationError(
                    _(
                        "Both paid_online and invoicing_method "
                        "fields can't be set at the same time."
                    )
                )
