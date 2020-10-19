# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import fields, models


class WIMResPartner(models.Model):
    _name = 'wim.res.partner'
    _inherit = 'wim.binding'
    _inherits = {'res.partner': 'odoo_id'}
    _description = 'WIM Partner'

    odoo_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner',
        required=True,
        index=True,
        ondelete='restrict',
    )
    external_id = fields.Char(related="odoo_id.customer_number")


class ResPartner(models.Model):
    _inherit = 'res.partner'

    wim_bind_ids = fields.One2many(
        comodel_name='wim.res.partner',
        inverse_name='odoo_id',
        copy=False,
        string='Partner Bindings',
        context={'active_test': False},
    )
