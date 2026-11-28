# Copyright 2018 ACSONE SA/NV
# Copyright 2026 Camptocamp SA
# @author Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import importlib.util
from datetime import timedelta
from pathlib import Path

from lxml import etree
from werkzeug.datastructures import EnvironHeaders
from werkzeug.exceptions import Unauthorized

from odoo import fields
from odoo.exceptions import AccessError, ValidationError
from odoo.tests.common import TransactionCase
from odoo.tools import file_open
from odoo.tools.safe_eval import datetime, safe_eval

from odoo.addons.website.tools import MockRequest

from ..models.auth_api_key import (
    HASH_KEYS_PARAM,
    HASHED_KEY_PLACEHOLDER,
    LAST_USED_THROTTLE,
)


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
            mocked_request.httprequest.environ["HTTP_API_KEY"] = "api_key"
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


class TestAuthApiKeyHashing(TransactionCase):
    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super().setUpClass(*args, **kwargs)
        cls.AuthApiKey = cls.env["auth.api.key"]
        cls.demo_user = cls.env.ref("base.user_demo")
        cls.param = cls.env["ir.config_parameter"].sudo()

    def _create(self, name, key):
        return self.AuthApiKey.create(
            {"name": name, "key": key, "user_id": self.demo_user.id}
        )

    def _uid(self, key):
        return self.AuthApiKey._retrieve_uid_from_api_key(key)

    def test_hashing_enabled_by_default(self):
        """A new key is stored hashed and can still be used."""
        api_key = self._create("hashed", "secret_key")
        self.assertEqual(api_key.key, HASHED_KEY_PLACEHOLDER)
        self.assertEqual(api_key.key_hash, self.AuthApiKey._hash_key("secret_key"))
        self.assertEqual(self._uid("secret_key"), self.demo_user.id)

    def test_hashed_key_is_not_the_placeholder(self):
        """The placeholder itself does not authenticate."""
        self._create("hashed", "secret_key")
        with self.assertRaises(ValidationError):
            self._uid(HASHED_KEY_PLACEHOLDER)

    def test_write_key_replaces_hash(self):
        """Writing a new key replaces the hash: the old key stops working."""
        api_key = self._create("hashed", "secret_key")
        api_key.key = "new_secret_key"
        self.assertEqual(api_key.key, HASHED_KEY_PLACEHOLDER)
        self.assertEqual(self._uid("new_secret_key"), self.demo_user.id)
        with self.assertRaises(ValidationError):
            self._uid("secret_key")

    def test_write_other_field_keeps_hash(self):
        """Writing another field does not touch the hashed key."""
        api_key = self._create("hashed", "secret_key")
        api_key.name = "renamed"
        self.assertEqual(self._uid("secret_key"), self.demo_user.id)

    def test_hashing_disabled(self):
        """With the hashing disabled the key is stored as is."""
        self.param.set_param(HASH_KEYS_PARAM, "False")
        api_key = self._create("plain", "secret_key")
        self.assertEqual(api_key.key, "secret_key")
        self.assertFalse(api_key.key_hash)
        self.assertEqual(self._uid("secret_key"), self.demo_user.id)

    def test_write_key_hashing_disabled_drops_hash(self):
        """A key written in plain text drops the hash of the previous one."""
        api_key = self._create("hashed", "secret_key")
        self.param.set_param(HASH_KEYS_PARAM, "False")
        api_key.key = "new_secret_key"
        self.assertFalse(api_key.key_hash)
        self.assertEqual(self._uid("new_secret_key"), self.demo_user.id)
        with self.assertRaises(ValidationError):
            self._uid("secret_key")

    def test_plain_key_still_works_when_enabling(self):
        """Keys stored in plain text keep working until they are hashed."""
        self.param.set_param(HASH_KEYS_PARAM, "False")
        api_key = self._create("plain", "secret_key")
        self.param.set_param(HASH_KEYS_PARAM, "True")
        self.assertEqual(self._uid("secret_key"), self.demo_user.id)
        self.assertEqual(api_key.key, "secret_key")

    def test_hash_plaintext_keys(self):
        """Hashing the existing keys keeps them usable but unreadable."""
        self.param.set_param(HASH_KEYS_PARAM, "False")
        api_key = self._create("plain", "secret_key")
        archived = self._create("archived", "archived_key")
        archived.active = False
        self.param.set_param(HASH_KEYS_PARAM, "True")
        self.AuthApiKey._hash_plaintext_keys()
        self.assertEqual(api_key.key, HASHED_KEY_PLACEHOLDER)
        self.assertEqual(archived.key, HASHED_KEY_PLACEHOLDER)
        self.assertEqual(self._uid("secret_key"), self.demo_user.id)

    def test_hash_plaintext_keys_disabled(self):
        """Nothing is hashed while the hashing is disabled."""
        self.param.set_param(HASH_KEYS_PARAM, "False")
        api_key = self._create("plain", "secret_key")
        self.AuthApiKey._hash_plaintext_keys()
        self.assertEqual(api_key.key, "secret_key")

    def test_settings_enable_hashes_existing_keys(self):
        """Enabling the setting hashes the keys already stored."""
        self.param.set_param(HASH_KEYS_PARAM, "False")
        api_key = self._create("plain", "secret_key")
        settings = self.env["res.config.settings"].create(
            {"auth_api_key_hash_keys": True}
        )
        settings.execute()
        self.assertEqual(api_key.key, HASHED_KEY_PLACEHOLDER)
        self.assertEqual(self._uid("secret_key"), self.demo_user.id)

    def test_neutralize(self):
        """The neutralization clears the hash too: no key works anymore."""
        self._create("hashed", "secret_key")
        with file_open("auth_api_key/data/neutralize.sql") as f:
            self.env.cr.execute(f.read())
        self.AuthApiKey.invalidate_model()
        self.env.registry.clear_cache()
        with self.assertRaises(ValidationError):
            self._uid("secret_key")
        self.assertFalse(self.AuthApiKey.search([("key_hash", "!=", False)]))

    def test_migration_keeps_plain_keys(self):
        """Existing keys: the upgrade keeps them stored in plain text."""
        # can be trashed on migration
        self.AuthApiKey.search([]).unlink()
        self.param.search([("key", "=", HASH_KEYS_PARAM)]).unlink()
        self._create("existing", "secret_key")
        self._run_migration()
        self.assertEqual(self.param.get_param(HASH_KEYS_PARAM), "False")
        self.assertFalse(self.AuthApiKey._keys_hashing_enabled())

    def test_migration_without_keys(self):
        """No existing keys: the upgrade leaves the default (hashing enabled)."""
        # can be trashed on migration
        self.AuthApiKey.search([]).unlink()
        self.param.search([("key", "=", HASH_KEYS_PARAM)]).unlink()
        self._run_migration()
        self.assertTrue(self.AuthApiKey._keys_hashing_enabled())

    def _run_migration(self):
        spec = importlib.util.spec_from_file_location(
            "post_migration",
            Path(__file__).parents[1] / "migrations/18.0.1.1.0/post-migration.py",
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.migrate(self.env.cr, "18.0.1.0.2")


class TestAuthApiKeyLastUsed(TransactionCase):
    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super().setUpClass(*args, **kwargs)
        cls.AuthApiKey = cls.env["auth.api.key"]
        cls.demo_user = cls.env.ref("base.user_demo")
        cls.api_key = cls.AuthApiKey.create(
            {"name": "good", "user_id": cls.demo_user.id, "key": "api_key"}
        )

    def _authenticate(self, key="api_key"):
        with MockRequest(self.env) as mocked_request:
            mocked_request.httprequest.environ["HTTP_API_KEY"] = key
            mocked_request.httprequest.environ["REMOTE_ADDR"] = "10.1.2.3"
            mocked_request.httprequest.headers = EnvironHeaders(
                mocked_request.httprequest.environ
            )
            return self.env["ir.http"]._auth_method_api_key()

    def test_last_used_set(self):
        """The first use of a key sets its last use date."""
        self.assertFalse(self.api_key.last_used_date)
        before = fields.Datetime.now()
        self.assertTrue(self._authenticate())
        self.assertGreaterEqual(self.api_key.last_used_date, before)

    def test_last_used_throttled(self):
        """A use right after the previous one does not update the date."""
        recent = fields.Datetime.now() - LAST_USED_THROTTLE / 2
        self.api_key.last_used_date = recent
        self.assertTrue(self._authenticate())
        self.assertEqual(self.api_key.last_used_date, recent)

    def test_last_used_updated(self):
        """A use after the throttle delay updates the date."""
        old = fields.Datetime.now() - LAST_USED_THROTTLE * 2
        self.api_key.last_used_date = old
        self.assertTrue(self._authenticate())
        self.assertGreater(self.api_key.last_used_date, old)

    def test_last_used_not_set_for_wrong_key(self):
        """A refused key leaves the last use date untouched."""
        with self.assertRaises(Unauthorized), self.assertLogs(
            "odoo.addons.auth_api_key.models.ir_http"
        ):
            self._authenticate("wrong")
        self.assertFalse(self.api_key.last_used_date)

    def _filter_names(self, filter_name, api_keys):
        """Return the names of ``api_keys`` matched by a filter of the search view."""
        arch = self.AuthApiKey.get_view(view_type="search")["arch"]
        node = etree.fromstring(arch).xpath(f"//filter[@name='{filter_name}']")[0]
        domain = safe_eval(
            node.get("domain"),
            {"context_today": fields.Date.today, "datetime": datetime},
        )
        found = self.AuthApiKey.search(domain + [("id", "in", api_keys.ids)])
        return set(found.mapped("name"))

    def test_search_not_used_filters(self):
        """The filters find the keys never used or not used for a given time."""
        now = fields.Datetime.now()
        api_keys = self.api_key  # never used
        for days in (5, 20, 45, 90):
            api_keys |= self.AuthApiKey.create(
                {
                    "name": f"used {days}d ago",
                    "user_id": self.demo_user.id,
                    "key": f"key_{days}",
                    "last_used_date": now - timedelta(days=days),
                }
            )
        self.assertEqual(self._filter_names("never_used", api_keys), {"good"})
        self.assertEqual(
            self._filter_names("not_used_10d", api_keys),
            {"good", "used 20d ago", "used 45d ago", "used 90d ago"},
        )
        self.assertEqual(
            self._filter_names("not_used_30d", api_keys),
            {"good", "used 45d ago", "used 90d ago"},
        )
        self.assertEqual(
            self._filter_names("not_used_60d", api_keys), {"good", "used 90d ago"}
        )
