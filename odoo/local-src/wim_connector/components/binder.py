# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo.addons.component.core import Component


class WimBinder(Component):
    _name = "wim.binder"
    _inherit = ["wim.base", "base.binder"]
