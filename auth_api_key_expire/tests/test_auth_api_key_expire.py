# Copyright 2026 Camptocamp SA
# @author Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from datetime import timedelta

from werkzeug.datastructures import EnvironHeaders
from werkzeug.exceptions import Unauthorized

from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase, new_test_user

from odoo.addons.website.tools import MockRequest

from ..models.auth_api_key import NOTIFY_GROUP_PARAM, WARNING_DAYS_PARAM

LOGGER = "odoo.addons.auth_api_key_expire.models.auth_api_key"


class TestAuthApiKeyExpire(TransactionCase):
    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super().setUpClass(*args, **kwargs)
        cls.AuthApiKey = cls.env["auth.api.key"]
        cls.demo_user = cls.env.ref("base.user_demo")
        cls.api_key = cls.AuthApiKey.create(
            {"name": "good", "user_id": cls.demo_user.id, "key": "api_key"}
        )
        cls.icp = cls.env["ir.config_parameter"].sudo()

    def _authenticate(self, key="api_key"):
        with MockRequest(self.env) as mocked_request:
            mocked_request.httprequest.environ["HTTP_API_KEY"] = key
            mocked_request.httprequest.environ["REMOTE_ADDR"] = "10.1.2.3"
            mocked_request.httprequest.headers = EnvironHeaders(
                mocked_request.httprequest.environ
            )
            return self.env["ir.http"]._auth_method_api_key()

    def test_no_expiration(self):
        """A key without expiration date does not expire."""
        self.assertEqual(
            self.AuthApiKey._retrieve_uid_from_api_key("api_key"), self.demo_user.id
        )

    def test_not_expired(self):
        """A key is accepted before its expiration date."""
        self.api_key.expiration_date = fields.Datetime.now() + timedelta(days=1)
        self.assertEqual(
            self.AuthApiKey._retrieve_uid_from_api_key("api_key"), self.demo_user.id
        )

    def test_expired(self):
        """A key is refused after its expiration date, even if it was cached."""
        self.assertEqual(
            self.AuthApiKey._retrieve_uid_from_api_key("api_key"), self.demo_user.id
        )
        self.api_key.expiration_date = fields.Datetime.now() - timedelta(seconds=1)
        with self.assertRaises(ValidationError) as cm, self.env.cr.savepoint():
            self.AuthApiKey._retrieve_uid_from_api_key("api_key")
        self.assertEqual(cm.exception.args[0], "The API key is expired")

    def test_expired_is_unauthorized(self):
        """An expired key gives a 401."""
        self.api_key.expiration_date = fields.Datetime.now() - timedelta(seconds=1)
        with (
            self.assertLogs("odoo.addons.auth_api_key.models.ir_http") as logs,
            self.assertRaises(Unauthorized),
        ):
            self._authenticate()
        self.assertEqual(
            logs.output,
            [
                "ERROR:odoo.addons.auth_api_key.models.ir_http:"
                "Wrong HTTP_API_KEY from 10.1.2.3, access denied"
            ],
        )

    def test_rotation(self):
        """The new key works while the old one is still valid, then alone."""
        new_key = self.AuthApiKey.create(
            {"name": "new", "user_id": self.demo_user.id, "key": "new_api_key"}
        )
        for key in ("api_key", "new_api_key"):
            self.assertEqual(
                self.AuthApiKey._retrieve_uid_from_api_key(key), self.demo_user.id
            )
        self.api_key.expiration_date = fields.Datetime.now() - timedelta(seconds=1)
        with self.assertRaises(ValidationError), self.env.cr.savepoint():
            self.AuthApiKey._retrieve_uid_from_api_key("api_key")
        self.assertEqual(
            self.AuthApiKey._retrieve_uid_from_api_key("new_api_key"),
            new_key.user_id.id,
        )

    def test_default_settings(self):
        """The data set the system administrators and 15 days by default."""
        self.assertEqual(
            self.env.ref("auth_api_key_expire.config_param_notify_group").value,
            str(self.env.ref("base.group_system").id),
        )
        self.assertEqual(
            self.env.ref("auth_api_key_expire.config_param_warning_days").value, "15"
        )


class TestAuthApiKeyExpireWarning(TransactionCase):
    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super().setUpClass(*args, **kwargs)
        cls.AuthApiKey = cls.env["auth.api.key"]
        cls.demo_user = cls.env.ref("base.user_demo")
        cls.icp = cls.env["ir.config_parameter"].sudo()
        cls.group = cls.env["res.groups"].create({"name": "API key managers"})
        cls.env["ir.model.access"].create(
            {
                "name": "API key managers can read the keys",
                "model_id": cls.env.ref("auth_api_key.model_auth_api_key").id,
                "group_id": cls.group.id,
                "perm_read": True,
            }
        )
        cls.manager1 = new_test_user(
            cls.env, login="manager1", groups="base.group_user"
        )
        cls.manager2 = new_test_user(
            cls.env, login="manager2", groups="base.group_user"
        )
        cls.managers = cls.manager1 | cls.manager2
        cls.managers.groups_id |= cls.group
        cls.icp.set_param(NOTIFY_GROUP_PARAM, cls.group.id)
        cls.api_key = cls._create_key("expiring", days=5)

    @classmethod
    def _create_key(cls, name, days):
        return cls.AuthApiKey.create(
            {
                "name": name,
                "key": f"key_{name}",
                "user_id": cls.demo_user.id,
                "expiration_date": fields.Datetime.now() + timedelta(days=days),
            }
        )

    def _activities(self, users=None):
        """Return the To Dos of the users (the managers by default)."""
        users = users or self.managers
        return self.env["mail.activity"].search([("user_id", "in", users.ids)])

    def test_one_activity_per_user(self):
        """Each member of the group gets one To Do on their contact."""
        self.AuthApiKey._cron_warn_expiring_keys()
        activities = self._activities()
        self.assertEqual(len(activities), 2)
        self.assertEqual(activities.user_id, self.managers)
        for activity in activities:
            self.assertEqual(activity.res_model, "res.partner")
            self.assertEqual(activity.res_id, activity.user_id.partner_id.id)
        self.assertEqual(
            activities.activity_type_id, self.env.ref("mail.mail_activity_data_todo")
        )
        self.assertEqual(
            set(activities.mapped("summary")), {"API keys about to expire"}
        )
        self.assertEqual(
            set(activities.mapped("date_deadline")),
            {self.api_key.expiration_date.date()},
        )
        self.assertTrue(self.api_key.expiration_warning_sent)

    def test_one_activity_for_all_keys(self):
        """A user is warned once for all the keys, the deadline is the first."""
        second = self._create_key("second", days=10)
        self.AuthApiKey._cron_warn_expiring_keys()
        activities = self._activities()
        self.assertEqual(len(activities), 2)
        for activity in activities:
            self.assertIn("expiring (user", activity.note)
            self.assertIn("second (user", activity.note)
            self.assertIn("auth_api_key.auth_api_key_act_window", activity.note)
            self.assertEqual(
                activity.date_deadline, self.api_key.expiration_date.date()
            )
        self.assertTrue(second.expiration_warning_sent)

    def test_later_key_has_its_own_activity(self):
        """A key coming close later is warned about in a new To Do."""
        self.AuthApiKey._cron_warn_expiring_keys()
        self._create_key("later", days=8)
        self.AuthApiKey._cron_warn_expiring_keys()
        self.assertEqual(len(self._activities()), 4)
        self.assertEqual(len(self._activities(self.manager1)), 2)

    def test_cron_is_idempotent(self):
        """Running the cron again does not duplicate the activities."""
        self.AuthApiKey._cron_warn_expiring_keys()
        self.AuthApiKey._cron_warn_expiring_keys()
        self.assertEqual(len(self._activities()), 2)

    def test_done_activity_not_recreated(self):
        """An activity marked as done is not created again."""
        self.AuthApiKey._cron_warn_expiring_keys()
        self._activities().action_done()
        self.AuthApiKey._cron_warn_expiring_keys()
        self.assertFalse(self._activities())

    def test_new_expiration_date_warns_again(self):
        """Changing the expiration date warns again when it comes close."""
        self.AuthApiKey._cron_warn_expiring_keys()
        self.api_key.expiration_date = fields.Datetime.now() + timedelta(days=100)
        self.assertFalse(self.api_key.expiration_warning_sent)
        self.api_key.expiration_date = fields.Datetime.now() + timedelta(days=3)
        self._activities().unlink()
        self.AuthApiKey._cron_warn_expiring_keys()
        self.assertEqual(len(self._activities()), 2)

    def test_not_close_enough(self):
        """A key expiring later than the warning delay is not warned about."""
        self.api_key.expiration_date = fields.Datetime.now() + timedelta(days=60)
        self.AuthApiKey._cron_warn_expiring_keys()
        self.assertFalse(self._activities())
        self.assertFalse(self.api_key.expiration_warning_sent)

    def test_warning_days_configurable(self):
        """The delay of the warning is configurable."""
        self.api_key.expiration_date = fields.Datetime.now() + timedelta(days=60)
        self.icp.set_param(WARNING_DAYS_PARAM, 90)
        self.AuthApiKey._cron_warn_expiring_keys()
        self.assertEqual(len(self._activities()), 2)

    def test_warning_disabled(self):
        """With a delay of 0 days nothing is sent."""
        self.icp.set_param(WARNING_DAYS_PARAM, 0)
        self.AuthApiKey._cron_warn_expiring_keys()
        self.assertFalse(self._activities())
        self.assertFalse(self.api_key.expiration_warning_sent)

    def test_expired_or_archived_not_warned(self):
        """Keys already expired, archived or without expiration are ignored."""
        self.api_key.unlink()
        expired = self._create_key("expired", days=-1)
        archived = self._create_key("archived", days=5)
        archived.active = False
        no_expiration = self.AuthApiKey.create(
            {"name": "forever", "key": "key_forever", "user_id": self.demo_user.id}
        )
        self.AuthApiKey._cron_warn_expiring_keys()
        self.assertFalse(self._activities())
        for api_key in (expired, archived, no_expiration):
            self.assertFalse(api_key.expiration_warning_sent)

    def test_default_group_is_system(self):
        """Without configuration the system administrators are warned."""
        self.icp.search([("key", "=", NOTIFY_GROUP_PARAM)]).unlink()
        users = self.AuthApiKey._get_expiration_warning_users()
        self.assertTrue(users)
        self.assertEqual(
            users,
            self.env.ref("base.group_system").users.filtered(
                lambda user: user.active and not user.share
            ),
        )

    def test_user_without_access_skipped(self):
        """A user of the group who cannot read the keys is skipped and logged."""
        self.env["ir.model.access"].search([("group_id", "=", self.group.id)]).unlink()
        reader = new_test_user(self.env, login="reader", groups="base.group_system")
        reader.groups_id |= self.group
        with self.assertLogs(LOGGER) as logs:
            self.AuthApiKey._cron_warn_expiring_keys()
        self.assertEqual(self._activities(self.managers | reader).user_id, reader)
        self.assertEqual(
            sorted(logs.output),
            [
                f"WARNING:{LOGGER}:User manager1 cannot read the API keys: "
                "not warned of their expiration",
                f"WARNING:{LOGGER}:User manager2 cannot read the API keys: "
                "not warned of their expiration",
            ],
        )
        self.assertTrue(self.api_key.expiration_warning_sent)

    def test_nobody_can_read(self):
        """Nobody able to read the keys: they are retried by the next run."""
        self.env["ir.model.access"].search([("group_id", "=", self.group.id)]).unlink()
        with self.assertLogs(LOGGER):
            self.AuthApiKey._cron_warn_expiring_keys()
        self.assertFalse(self._activities())
        self.assertFalse(self.api_key.expiration_warning_sent)

    def test_nobody_to_warn(self):
        """Nobody in the group: a warning is logged, the key will be retried."""
        self.group.users = False
        with self.assertLogs(LOGGER) as logs:
            self.AuthApiKey._cron_warn_expiring_keys()
        self.assertEqual(
            logs.output,
            [
                f"WARNING:{LOGGER}:No user to warn about the API keys about to "
                "expire: expiring"
            ],
        )
        self.assertFalse(self.api_key.expiration_warning_sent)

    def test_settings(self):
        """The group and the delay are set from the settings."""
        group = self.env["res.groups"].create({"name": "Other managers"})
        settings = self.env["res.config.settings"].create(
            {
                "auth_api_key_expire_group_id": group.id,
                "auth_api_key_expire_warning_days": 30,
            }
        )
        settings.execute()
        self.assertEqual(int(self.icp.get_param(NOTIFY_GROUP_PARAM)), group.id)
        self.assertEqual(self.AuthApiKey._get_expiration_warning_days(), 30)

    def test_search_filters(self):
        """The filters find the expired keys and the ones being warned about."""
        arch = self.AuthApiKey.get_view(view_type="search")["arch"]
        for name in ("expired", "expiring", "never_used", "not_used_10d"):
            self.assertIn(f'name="{name}"', arch)
