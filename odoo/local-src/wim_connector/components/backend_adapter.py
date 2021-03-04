# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
# import httplib
import datetime
import json
import logging
from contextlib import contextmanager
from urllib.parse import urljoin

from odoo import api, registry
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

    @contextmanager
    @api.model
    def _do_in_new_env(self):
        reg = registry(self.env.cr.dbname)
        with api.Environment.manage(), reg.cursor() as new_cr:
            yield api.Environment(new_cr, self.env.uid, self.env.context)

    def write(self, external_id, data):
        """ Update records on the external system """
        endpoint = self._endpoint_mapping["write"]
        uri = urljoin(self.backend_record.uri, endpoint)
        json_data = json.dumps(data)
        job_log_id = False
        uuid = self.env.context.get("job_uuid")
        if uuid:
            # If job fails, everything's rollbacked.
            # To create log instances, we have to instanciate a new environment.
            with self._do_in_new_env() as new_env:
                job = (
                    new_env["queue.job"]
                    .sudo()
                    .search([("uuid", "=", uuid)], limit=1)
                )
                now = datetime.datetime.now()
                log_data = "uri: {}\ncontent: {}".format(uri, json_data)
                job_log = (
                    new_env["queue.job.log"]
                    .sudo()
                    .create(
                        {
                            "queue_job_id": job.id,
                            "datetime_query": now,
                            "data": log_data,
                        }
                    )
                )
                job_log_id = job_log.id
        response = self.client.post(uri, json_data)
        if job_log_id:
            job_log = self.env["queue.job.log"].sudo().browse(job_log_id)
            job_log.write(
                {
                    "state": "success" if response.ok else "failed",
                    "result": response.text,
                }
            )
