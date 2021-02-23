# Copyright 2021 Camptocamp SA
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl)
from odoo import models


class SaleOrder(models.Model):

    _inherit = "sale.order"

    def update_existing_subscriptions(self):
        # Ensure specific renewal behaviour is triggered only from sale order
        # confirmation on closed subscription
        std_ids = []
        old_sub_renewal_ids = []
        for order in self:
            if order.subscription_management != "renew" or any(
                order.order_line.mapped('subscription_id.in_progress')
            ):
                std_ids.append(order.id)
            else:
                old_sub_renewal_ids.append(order.id)
        if std_ids:
            std_orders = self.browse(std_ids)
            res = super(SaleOrder, std_orders).update_existing_subscriptions()
        else:
            res = []
        if old_sub_renewal_ids:
            old_sub_renewal_orders = self.browse(
                old_sub_renewal_ids
            ).with_context(_reset_sub_dates=True)
            res += super(
                SaleOrder, old_sub_renewal_orders
            ).update_existing_subscriptions()
        return res
