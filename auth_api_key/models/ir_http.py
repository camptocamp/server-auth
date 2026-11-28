# Copyright 2018 ACSONE SA/NV
# Copyright 2017 Akretion (http://www.akretion.com).
# Copyright 2026 Camptocamp SA
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# @author Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import logging

from werkzeug.exceptions import Unauthorized

from odoo import models
from odoo.exceptions import ValidationError
from odoo.http import request

_logger = logging.getLogger(__name__)


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    @classmethod
    def _auth_method_api_key(cls):
        headers = request.httprequest.headers
        api_key = headers.get("API_KEY")
        if api_key:
            request.update_env(user=1)
            try:
                auth_api_key = request.env["auth.api.key"]._retrieve_api_key(api_key)
            except ValidationError:
                # Unknown key: answer 401 like for a missing one, not a user error.
                auth_api_key = None
            if auth_api_key:
                auth_api_key._update_last_used()
                # reset _env on the request since we change the uid...
                # the next call to env will instantiate an new
                # odoo.api.Environment with the user defined on the
                # auth.api_key
                request._env = None
                request.update_env(user=auth_api_key.user_id.id)
                request.auth_api_key = api_key
                request.auth_api_key_id = auth_api_key.id
                return True
        _logger.error(
            "Wrong HTTP_API_KEY from %s, access denied",
            request.httprequest.environ.get("REMOTE_ADDR"),
        )
        raise Unauthorized()
