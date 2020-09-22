# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo.addons.component.core import Component
from odoo.addons.component_event import skip_if
from odoo.addons.connector.components.mapper import mapping


class WIMResPartnerListener(Component):
    _name = 'wim.res.partner.listener'
    _inherit = ['base.connector.listener']
    _apply_on = ['wim.res.partner']

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_create(self, record, fields=None):
        # if record.sync_action == 'export':
        record.with_delay(priority=10).export_record(fields=fields)

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_write(self, record, fields=None):
        # if record.sync_action == 'export':
        record.with_delay(priority=10).export_record(fields=fields)


class ResPartnerListener(Component):
    _name = 'res.partner.listener'
    _inherit = ['base.connector.listener']
    _apply_on = ['res.partner']

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_write(self, record, fields=None):
        if fields == ['wim_bind_ids'] or fields == ['message_follower_ids']:
            # When vals is wim_bind_ids:
            # Binding edited from the record's view. When only this field has
            # been modified, an other job has already been delayed for the
            # binding record so can exit this event early.

            # When vals is message_follower_ids:
            # MailThread.message_subscribe() has been called, this
            # method does a write on the field message_follower_ids,
            # we never want to export that.
            return
        for binding in record.wim_bind_ids:
            # if binding.sync_action == 'export':
            binding.with_delay(priority=10).export_record(fields=fields)


class WimResPartnerExportMapper(Component):

    _name = "wim.res.partner.export.mapper"
    _inherit = ["wim.base", "base.export.mapper"]

    @mapping
    def map_fields(self, record):
        return {"name": record.name}
