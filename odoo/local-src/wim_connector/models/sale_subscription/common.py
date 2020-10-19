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


class SaleSubscriptionStage(models.Model):

    _inherit = "sale.subscription.stage"

    in_progress = fields.Boolean(
        help="Defines if the record is considered as active on WIM."
    )
