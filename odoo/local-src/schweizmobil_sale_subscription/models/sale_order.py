# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import fields,models


class SaleOrder(models.Model):

    _name = "sale.order"
    _inherit = ["sale.order", "sale.payment.fields.mixin"]

    customer_number = fields.Char(related="partner_id.customer_number")

    def _prepare_invoice(self):
        res = super()._prepare_invoice()
        res.update(
            {
                "invoicing_method": self.invoicing_method,
                "paid_online": self.paid_online,
            }
        )
        return res
