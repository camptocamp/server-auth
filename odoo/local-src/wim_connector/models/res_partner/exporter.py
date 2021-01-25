# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo.addons.component.core import Component
from odoo.addons.component_event import skip_if
from odoo.addons.connector.components.mapper import changed_by, mapping

LANG_MAPPING = {"de_CH": "de", "fr_CH": "fr", "en_US": "en", "it_IT": "it"}


class WIMResPartnerWebserviceAdapter(Component):

    _name = "wim.res.partner.webservice.adapter"
    _inherit = "wim.webservice.adapter"
    _apply_on = "wim.res.partner"

    _endpoint_mapping = {"write": "updatemember"}


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
    _inherit = ["base.export.mapper", "wim.base"]
    _apply_on = "wim.res.partner"

    _direct = [
        ("name", "name"),
        ("swisspass_customerid", "swissPassCustomerId"),
        ("firstname", "firstName"),
        ("lastname", "lastName"),
        ("newsletter", "newsletter"),
    ]

    @changed_by(
        "name",
        "swisspass_customerid",
        "firstname",
        "lastname",
        "newsletter",
        "street",
        "street2",
        "zip",
        "city",
        "title",
        "lang",
        "country_id",
    )
    @mapping
    def map_customer_number(self, record):
        return {"customerNr": record.customer_number}

    @changed_by(
        "name",
        "swisspass_customerid",
        "firstname",
        "lastname",
        "newsletter",
        "street",
        "street2",
        "zip",
        "city",
        "title",
        "lang",
        "country_id",
    )
    @mapping
    def map_member(self, record):
        member_data = {}
        for odoo_field, external_field in self._direct:
            member_data[external_field] = record[odoo_field] or None
        member_data.update(self.map_address(record))
        member_data.update(self.map_gender_code(record))
        member_data.update(self.map_lang_code(record))
        member_data.update(self.map_newsletter(record))
        if member_data:
            member_data.update(
                {"customerNr": record.customer_number, "email": record.email}
            )
            return {"member": member_data}
        return {}

    def map_gender_code(self, record):
        title_mapping = {
            self.env.ref("base.res_partner_title_madam").id: "f",
            self.env.ref("base.res_partner_title_mister").id: "m",
        }
        return {"genderCode": title_mapping.get(record.title.id, "n")}

    def map_lang_code(self, record):
        return {"languageCode": LANG_MAPPING.get(record.lang)}

    def map_address(self, record):
        mapping_methods = [
            self.map_street,
            self.map_addendum,
            self.map_zip,
            self.map_city,
            self.map_country_code,
        ]
        address_vals = {}
        for mapping_method in mapping_methods:
            address_vals.update(mapping_method(record))
        return {"address": address_vals}

    # sub-object, should not be decorated with @mapping

    def map_street(self, record):
        res = {"houseNumber": None, "street": None}
        if record.street:
            split_street = record.street.split()
            if len(split_street) < 2:
                res["street"] = record.street
            else:
                res["houseNumber"] = split_street[-1]
                res["street"] = " ".join(split_street[:-1])
        return res

    def map_addendum(self, record):
        return {"addendum": record.street2 or None}

    def map_city(self, record):
        return {"city": record.city or None}

    def map_zip(self, record):
        return {"zip": record.zip or None}

    def map_country_code(self, record):
        return {"countryCode": record.country_id.code or None}

    def map_newsletter(self, record):
        return {"newsletter": record.newsletter}
