# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo.addons.component.core import Component


class WimExporter(Component):

    _name = "wim.exporter"
    _inherit = ["wim.base", "generic.exporter"]
    _default_binding_field = "wim_bind_ids"
    _usage = "record.exporter"
