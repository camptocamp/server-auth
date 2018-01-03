##############################################################################
#
#    Author: Laurent Mignon
#    Copyright 2014 'ACSONE SA/NV'
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import odoo
from odoo import fields, models
from odoo.addons.auth_from_http_remote_user import utils


class Users(models.Model):
    _inherit = 'res.users'

    sso_key = fields.Char('SSO Key', size=utils.KEY_LENGTH,
                          readonly=True)

    def copy(self, default=None):
        default = default = {} if default is None else default
        default['sso_key'] = False
        return super(Users, self).copy(default)

    def check_credentials(self, password):
        res = self.sudo().search([('id', '=', self._uid),
                                  ('sso_key', '=', password)])
        if not res:
            try:
                return super(Users, self).check_credentials(password)
            except odoo.exceptions.AccessDenied:
                raise odoo.exceptions.AccessDenied()

    @classmethod
    def check(cls, db, uid, passwd):
        try:
            return super(Users, cls).check(db, uid, passwd)
        except odoo.exceptions.AccessDenied:
            if not passwd:
                raise
            registry = odoo.registry(db)
            with registry.cursor() as cr:
                cr.execute('''SELECT COUNT(1)
                                FROM res_users
                               WHERE id=%s
                                 AND sso_key=%s
                                 AND active=%s''', (int(uid), passwd, True))
                if not cr.fetchone()[0]:
                    raise
                cls._uid_cache.setdefault(db, {})[uid] = passwd

    @classmethod
    def find_uid_from_iamuserid(cls, db='', login=''):
        """Find the odoo user id for a specific login """
        registry = odoo.registry(db)
        with registry.cursor() as cr:
            cr.execute('''SELECT id
                            FROM res_users
                           WHERE login=%s''', (login,))
            row = cr.fetchone()
            if row:
                if len(row) > 0:
                    return row[0]
        return None
