# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
# import httplib
import logging

from odoo.addons.component.core import Component

_logger = logging.getLogger(__name__)

# Add detailed logs
# httplib.HTTPConnection.debuglevel = 1
# requests_log = logging.getLogger("requests.packages.urllib3")
# requests_log.setLevel(logging.DEBUG)
# requests_log.propagate = True


class WIMWebserviceAdapter(Component):
    """ Generic adapter for using the WIM backend """

    _name = 'wim.webservice.adapter'
    _inherit = ['base.backend.adapter.crud', 'wim.base']
    _usage = 'backend.adapter'

    def __init__(self, work_context):
        super().__init__(work_context)
        self._client = None

    @property
    def client(self):
        # lazy load the client, initialize only when actually needed
        if not self._client:
            self._client = self.backend_record.get_api_client()
        return self._client

    # TODO Check if needed
    # def create(self, *args, **kwargs):
    #     """ Create a record on the external system """
    #     raise NotImplementedError

    def write(self, external_id, data):
        """ Update records on the external system """
        data.update({"customerNr": external_id})
        req_data = {"member": data}
        self.client.post(self.backend_record.uri + "/changeadress", req_data)
