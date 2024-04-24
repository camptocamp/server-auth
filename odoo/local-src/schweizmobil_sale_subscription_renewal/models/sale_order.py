# Copyright 2021 Camptocamp SA
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl)
from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _prepare_upsell_renew_order_values(self, subscription_state):
        vals = super()._prepare_upsell_renew_order_values(subscription_state)
        if subscription_state == '2_renewal':
            for subscription in self:
                payment_term = subscription._get_renewal_payment_term()
                if payment_term:
                    vals["payment_term_id"] = payment_term.id
                vals.update(
                    {
                        'user_id': self.env.uid,
                        'online_renewal': 'none',
                        'to_close': False,
                    }
                )
        return vals

    def _get_renewal_payment_term(self):
        """Hook allowing to redefine payment term for renewal orders"""
        self.ensure_one()
        return self.env["account.payment.term"].browse()
