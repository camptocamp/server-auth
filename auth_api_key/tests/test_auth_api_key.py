# Copyright 2018 ACSONE SA/NV
# Copyright 2026 Camptocamp SA
# @author Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from werkzeug.datastructures import EnvironHeaders
from werkzeug.exceptions import Unauthorized

from odoo.exceptions import AccessError, ValidationError
from odoo.tests.common import TransactionCase

from odoo.addons.website.tools import MockRequest


class TestAuthApiKey(TransactionCase):
    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super().setUpClass(*args, **kwargs)
        cls.AuthApiKey = cls.env["auth.api.key"]
        cls.demo_user = cls.env.ref("base.user_demo")
        cls.api_key_good = cls.AuthApiKey.create(
            {"name": "good", "user_id": cls.demo_user.id, "key": "api_key"}
        )

    def test_lookup_key_from_db(self):
        demo_user = self.env.ref("base.user_demo")
        self.assertEqual(
            self.env["auth.api.key"]._retrieve_uid_from_api_key("api_key"), demo_user.id
        )

    def test_wrong_key(self):
        with self.assertRaises(ValidationError), self.env.cr.savepoint():
            self.env["auth.api.key"]._retrieve_uid_from_api_key("api_wrong_key")

    def test_user_not_allowed(self):
        # only system users can check for key
        with self.assertRaises(AccessError), self.env.cr.savepoint():
            self.env["auth.api.key"].with_user(
                user=self.demo_user
            )._retrieve_uid_from_api_key("api_wrong_key")

    def test_cache_invalidation(self):
        self.assertEqual(
            self.env["auth.api.key"]._retrieve_uid_from_api_key("api_key"),
            self.demo_user.id,
        )
        self.api_key_good.write({"key": "updated_key"})
        self.assertEqual(
            self.env["auth.api.key"]._retrieve_uid_from_api_key("updated_key"),
            self.demo_user.id,
        )
        with self.assertRaises(ValidationError):
            self.env["auth.api.key"]._retrieve_uid_from_api_key("api_key")

    def test_user_archived_unarchived_with_option_on(self):
        self.env.company.archived_user_disable_auth_api_key = True
        demo_user = self.env.ref("base.user_demo")
        self.assertEqual(
            self.env["auth.api.key"]._retrieve_uid_from_api_key("api_key"), demo_user.id
        )
        demo_user.active = False
        with self.assertRaises(ValidationError):
            self.env["auth.api.key"]._retrieve_uid_from_api_key("api_key")
        demo_user.active = True
        self.assertEqual(
            self.env["auth.api.key"]._retrieve_uid_from_api_key("api_key"), demo_user.id
        )

    def test_user_archived_unarchived_with_option_off(self):
        self.env.company.archived_user_disable_auth_api_key = False
        demo_user = self.env.ref("base.user_demo")
        self.assertEqual(
            self.env["auth.api.key"]._retrieve_uid_from_api_key("api_key"), demo_user.id
        )
        demo_user.active = False
        self.assertEqual(
            self.env["auth.api.key"]._retrieve_uid_from_api_key("api_key"), demo_user.id
        )

    def test_api_key_headers(self):
        """The API key in the headers is read."""
        with MockRequest(self.env) as mocked_request:
            mocked_request.httprequest.environ["HTTP_API_KEY"] = self.api_key_good.key
            mocked_request.httprequest.headers = EnvironHeaders(
                mocked_request.httprequest.environ
            )
            self.assertTrue(self.env["ir.http"]._auth_method_api_key())

    def test_unlink_cache_invalidation(self):
        """A deleted key stops being accepted right away."""
        uid = self.env["auth.api.key"]._retrieve_uid_from_api_key("api_key")
        self.assertEqual(uid, self.demo_user.id)
        self.api_key_good.unlink()
        with self.assertRaises(ValidationError):
            self.env["auth.api.key"]._retrieve_uid_from_api_key("api_key")

    def test_archive_cache_invalidation(self):
        """An archived key stops being accepted right away."""
        uid = self.env["auth.api.key"]._retrieve_uid_from_api_key("api_key")
        self.assertEqual(uid, self.demo_user.id)
        self.api_key_good.active = False
        with self.assertRaises(ValidationError):
            self.env["auth.api.key"]._retrieve_uid_from_api_key("api_key")
        self.api_key_good.active = True
        uid = self.env["auth.api.key"]._retrieve_uid_from_api_key("api_key")
        self.assertEqual(uid, self.demo_user.id)

    def test_wrong_key_message_does_not_leak_key(self):
        """The error raised for an unknown key does not contain the key."""
        with self.assertRaises(ValidationError) as cm, self.env.cr.savepoint():
            self.env["auth.api.key"]._retrieve_uid_from_api_key("secret_typo")
        self.assertEqual(cm.exception.args[0], "The API key is not allowed")

    def test_wrong_key_is_unauthorized(self):
        """An unknown key gives a 401 and logs the caller address, not the key."""
        with MockRequest(self.env) as mocked_request:
            mocked_request.httprequest.environ["HTTP_API_KEY"] = "secret_typo"
            mocked_request.httprequest.environ["REMOTE_ADDR"] = "10.1.2.3"
            mocked_request.httprequest.headers = EnvironHeaders(
                mocked_request.httprequest.environ
            )
            with (
                self.assertLogs("odoo.addons.auth_api_key.models.ir_http") as logs,
                self.assertRaises(Unauthorized),
            ):
                self.env["ir.http"]._auth_method_api_key()
        self.assertEqual(
            logs.output,
            [
                "ERROR:odoo.addons.auth_api_key.models.ir_http:"
                "Wrong HTTP_API_KEY from 10.1.2.3, access denied"
            ],
        )

    def test_missing_key_is_unauthorized(self):
        """A request without key gives a 401."""
        with MockRequest(self.env) as mocked_request:
            mocked_request.httprequest.environ["REMOTE_ADDR"] = "10.1.2.3"
            mocked_request.httprequest.headers = EnvironHeaders(
                mocked_request.httprequest.environ
            )
            with (
                self.assertLogs("odoo.addons.auth_api_key.models.ir_http") as logs,
                self.assertRaises(Unauthorized),
            ):
                self.env["ir.http"]._auth_method_api_key()
        self.assertEqual(
            logs.output,
            [
                "ERROR:odoo.addons.auth_api_key.models.ir_http:"
                "Wrong HTTP_API_KEY from 10.1.2.3, access denied"
            ],
        )
