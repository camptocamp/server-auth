# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import _, exceptions
from odoo.addons.component.core import Component
from odoo.addons.component_event import skip_if
from odoo.addons.connector.components.mapper import changed_by, mapping

ALLOWED_LANG_VALUES = ["de", "fr", "en", "it"]


class WIMResPartnerWebserviceAdapter(Component):

    _name = "wim.res.partner.webservice.adapter"
    _inherit = "wim.webservice.adapter"
    _apply_on = "wim.res.partner"

    _endpoint_mapping = {"write": "updatemember"}


class ResPartnerListener(Component):
    _name = 'res.partner.listener'
    _inherit = ['base.connector.listener']
    _apply_on = ['res.partner']

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
        return (
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
            "email",
        )

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_write(self, record, fields=None):
        if self._no_trigger_fields_modified(fields):
            # Do not create a job when no modified field is a trigger field
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
        "email",
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
        "email",
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
        language_code = record.lang.split("_")[0]
        if language_code not in ALLOWED_LANG_VALUES:
            raise exceptions.UserError(
                _("Partner lang {} is not valid.").format(record.lang)
            )
        return {"languageCode": language_code}

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
