# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import fields, models


class WIMSaleSubscription(models.Model):
    _name = 'wim.sale.subscription'
    _inherit = 'wim.binding'
    _inherits = {'sale.subscription': 'odoo_id'}
    _description = 'WIM Subscription'

    odoo_id = fields.Many2one(
        comodel_name='sale.subscription',
        string='Subscription',
        required=True,
        index=True,
        ondelete='restrict',
    )
    external_id = fields.Char(related="odoo_id.partner_id.customer_number")


class SaleSubscription(models.Model):
    _inherit = 'sale.subscription'

    wim_bind_ids = fields.One2many(
        comodel_name='wim.sale.subscription',
        inverse_name='odoo_id',
        copy=False,
        string='Subscription Bindings',
        context={'active_test': False},
    )

    def _prepare_invoice_data(self):
        """
        Apply distinct payment term for subscriptions and sale orders.
        """
        res = super()._prepare_invoice_data()
        if self.wim_bind_ids:
            backend = self.env.ref("wim_connector.wim_backend_config")
            payment_term = backend.recurring_invoice_payment_term_id
            res.update(invoice_payment_term_id=payment_term.id)
        return res


class SaleSubscriptionStage(models.Model):

    _inherit = "sale.subscription.stage"

    in_progress = fields.Boolean(
        help="Defines if the record is considered as active on WIM."
    )
