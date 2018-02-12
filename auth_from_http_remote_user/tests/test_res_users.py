# Author: Laurent Mignon
# Copyright 2014-2018 'ACSONE SA/NV'
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import api, registry
from odoo.tests import common
from odoo.tests.common import TransactionCase
import mock
import os
from contextlib import contextmanager
import unittest


@contextmanager
def mock_cursor(cr):
    with mock.patch('openerp.sql_db.Connection.cursor') as mocked_cursor_call:
        org_close = cr.close
        org_autocommit = cr.autocommit
        try:
            cr.close = mock.Mock()
            cr.autocommit = mock.Mock()
            mocked_cursor_call.return_value = cr
            yield
        finally:
            cr.close = org_close
    cr.autocommit = org_autocommit


class TestResUsers(TransactionCase):

    def setUp(self):
        super().setUp()
        self.user = self.env['res.users'].browse(1)
        self._model = self.env['res.users']

    def test_authenticate(self):
        """ Try creating a key for the user """
        key = self._model.logging_sso_user(self.env, self.user)
        self.assertEqual(self.user.sso_key, key)

    def test_login(self):
        reg = registry(self.env.cr.dbname)
        with api.Environment.manage():
            with reg.cursor() as cr:
                env = api.Environment(cr, self._uid, {})
                env['res.users'].browse(1).write({'sso_key': False})

        res_users_obj = self.env['res.users']
        res = res_users_obj.authenticate(
            common.get_db_name(), 'admin', 'admin', None)
        uid = res
        self.assertTrue(res, "Basic login must works as expected")
        token = "123456"
        res = res_users_obj.authenticate(
            common.get_db_name(), 'admin', token, None)
        self.assertFalse(res)
        # mimic what the new controller do when it finds a value in
        # the http header (HTTP_REMOTE_USER)
        user = self.env['res.users'].browse([uid])
        user.write({'sso_key': token})

        # Here we need to mock the cursor since the login is natively done
        # inside its own connection
        with mock_cursor(self.cr):
            # Verify that the given (uid, token) is authorized for the database
            self.env['res.users'].sudo().check(
                common.get_db_name(), uid, token)
            # We are able to login with the new token
            res = res_users_obj.authenticate(
                common.get_db_name(), 'admin', token, None)
            self.assertTrue(res)

    @unittest.skipIf(os.environ.get('TRAVIS'),
                     'When run by travis, tests runs on a database with all '
                     'required addons from server-tools and their dependencies'
                     ' installed. Even if `auth_from_http_remote_user` does '
                     'not require the `mail` module, The previous installation'
                     ' of the mail module has created the column '
                     '`notification_email_send` as REQUIRED into the table '
                     'res_partner. BTW, it\'s no more possible to copy a '
                     'res_user without an integrity error')
    def test_copy(self):
        '''Check that the sso_key is not copied on copy
        '''
        vals = {'sso_key': '123'}
        user = self.env['res.users'].browse(self.uid)
        user.write(vals)
        read_vals = user.read(['sso_key'])[0]
        self.assertDictContainsSubset(vals, read_vals)
        copy = user.copy()
        read_vals = copy.read(['sso_key'])[0]
        self.assertFalse(read_vals.get('sso_key'))
