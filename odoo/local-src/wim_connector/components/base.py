# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo.addons.component.core import AbstractComponent


class BaseWIMConnectorComponent(AbstractComponent):
    """Base WIM Connector Component
    All components of this connector should inherit from it.
    """

    _name = 'wim.base'
    _inherit = 'base.connector'
    _collection = 'wim.backend'
