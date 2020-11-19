# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import models


class SaleOrder(models.Model):

    _name = "sale.order"
    _inherit = ["sale.order", "wim.payment.fields.mixin"]

    def _prepare_invoice(self):
        res = super()._prepare_invoice()
        res.update(
            {
                "invoicing_method": self.invoicing_method,
                "paid_online": self.paid_online,
            }
        )
        return res
