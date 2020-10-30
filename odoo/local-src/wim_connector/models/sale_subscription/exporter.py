# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo.addons.component.core import Component
from odoo.addons.component_event import skip_if
from odoo.addons.connector.components.mapper import changed_by, mapping

WIM_DATE_FORMAT = "%d.%m.%Y"


class WIMSaleSubscriptionWebserviceAdapter(Component):

    _name = "wim.sale.subscription.webservice.adapter"
    _inherit = "wim.webservice.adapter"
    _apply_on = "wim.sale.subscription"

    _endpoint_mapping = {"write": "updatemembership"}


class SaleSubscriptionListener(Component):
    _name = 'sale.subscription.listener'
    _inherit = ['base.connector.listener']
    _apply_on = ['sale.subscription']

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


class WimSaleSubscriptionMapper(Component):

    _name = "wim.sale.subscription.export.mapper"
    _inherit = ["base.export.mapper", "wim.base"]
    _apply_on = "wim.sale.subscription"

    def map_valid_from(self, record):
        return {"validFrom": record.date_start.strftime(WIM_DATE_FORMAT)}

    def map_valid_until(self, record):
        return {"validUntil": record.date.strftime(WIM_DATE_FORMAT)}

    def map_active(self, record):
        return {"active": record.in_progress}

    @changed_by("date_start", "date", "stage_id")
    @mapping
    def map_customer_number(self, record):
        customer_number = record.partner_id.customer_number
        # TODO If empty raise something
        return {"customerNr": customer_number}

    @changed_by("date_start", "date", "stage_id")
    @mapping
    def map_membership(self, record):
        membership_data = {}
        mapping_methods = [
            self.map_valid_from,
            self.map_valid_until,
            self.map_active,
        ]
        for mapping_method in mapping_methods:
            membership_data.update(mapping_method(record))
        return {"membership": membership_data}
