# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo.addons.component.core import AbstractComponent, Component


class WimExporter(Component):

    _name = "wim.exporter"
    _inherit = ["wim.base", "generic.exporter"]
    _default_binding_field = "wim_bind_ids"
    _usage = "record.exporter"


class ConnectorListener(AbstractComponent):

    _inherit = "base.connector.listener"

    def _no_trigger_fields_modified(self, fields):
        """
        Returns False if any trigger field has been modified
        """
        for field in fields:
            if field in self.trigger_fields:
                return False
        return True
