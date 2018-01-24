# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import http, registry
from odoo.http import request

from odoo.addons.auth_from_http_remote_user.controllers import main

import logging

_logger = logging.getLogger(__name__)


class Home(main.Home):

    _REMOTE_USER_ROLE = 'HTTP_USER_ROLES'
    _REMOTE_USER_ROLE_SEPARATOR = ','

    def _get_roles(self):
        """Return user roles from HTTP header.

        Return in a list the user role codes found in the HTTP
        header using the field and separator predefined.
        """
        roles = []
        headers = http.request.httprequest.headers.environ
        roles_in_header = headers.get(self._REMOTE_USER_ROLE, None)
        if roles_in_header:
            roles = roles_in_header.split(self._REMOTE_USER_ROLE_SEPARATOR)
        return roles

    def _authenticate_user(self, user, cr):
        """Update roles assigned to user """
        cr.execute('''DELETE FROM res_users_role_line
                        WHERE user_id=%s''', [user.id])
        role_codes = self._get_roles()
        if role_codes:
            roles = request.env['res.users.role'].sudo().search(
                    [('user_role_code', 'in', role_codes)])
            _logger.info('''Role codes {} found ids {} assigning to {}'''
                    .format( role_codes, roles.ids, user.login))
            if roles:
                cr.execute('''INSERT INTO res_users_role_line(user_id, role_id)
                                VALUES( %s, unnest( %s))''',
                           (user.id, list(roles.ids)))
        else:
            _logger.warn('No HTTP user roles found for {} '.format(user.login))

        return super()._authenticate_user(user, cr)
