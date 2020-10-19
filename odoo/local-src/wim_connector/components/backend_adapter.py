# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
# import httplib
import logging
from urllib.parse import urljoin

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

    _endpoint_mapping = {}

    def __init__(self, work_context):
        super().__init__(work_context)
        self._client = None

    @property
    def client(self):
        # lazy load the client, initialize only when actually needed
        if not self._client:
            self._client = self.backend_record.get_api_client()
        return self._client

    def write(self, external_id, data):
        """ Update records on the external system """
        endpoint = self._endpoint_mapping["write"]
        uri = urljoin(self.backend_record.uri, endpoint)
        self.client.post(uri, data)
