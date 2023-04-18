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

    _trigger_fields = None

    @property
    def trigger_fields(self):
        """
        Gets a set of fields that triggers an export
        based on mapper's changed_by fields
        """
        # TODO : find a way to get the mapper
        # if not self._trigger_fields:
        #     mapper = self.component(usage="mapper")
        #     self._trigger_fields = mapper.changed_by_fields()
        # return self._trigger_fields
        return ("date_start", "date", "stage_id", "next_online_renewal_date")

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_write(self, record, fields=None):
        eta = self.env.context.get("job_export_eta")
        if self._no_trigger_fields_modified(fields):
            # Do not create a job when no modified field is a trigger field
            return
        for binding in record.wim_bind_ids:
            # if binding.sync_action == 'export':
            binding.with_delay(priority=10, eta=eta).export_record(
                fields=fields
            )


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

    def map_start_of_renewal_period(self, record):
        date = record.next_online_renewal_date
        res = {
            "startOfRenewalPeriod": date.strftime(WIM_DATE_FORMAT)
            if date
            else ""
        }
        return res

    # TODO : If needs to be updated, update trigger_fields() as well
    @changed_by("date_start", "date", "stage_id", "next_online_renewal_date")
    @mapping
    def map_customer_number(self, record):
        customer_number = record.partner_id.customer_number
        # TODO If empty raise something
        return {"customerNr": customer_number}

    # TODO : If needs to be updated, update trigger_fields() as well
    @changed_by("date_start", "date", "stage_id", "next_online_renewal_date")
    @mapping
    def map_membership(self, record):
        membership_data = {}
        mapping_methods = [
            self.map_valid_from,
            self.map_valid_until,
            self.map_active,
            self.map_start_of_renewal_period,
        ]
        for mapping_method in mapping_methods:
            membership_data.update(mapping_method(record))
        return {"membership": membership_data}
