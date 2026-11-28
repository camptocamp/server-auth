# Copyright 2026 Camptocamp SA
# @author Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import logging
from datetime import timedelta

from markupsafe import Markup

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

NOTIFY_GROUP_PARAM = "auth_api_key_expire.notify_group_id"
WARNING_DAYS_PARAM = "auth_api_key_expire.warning_days"


class AuthApiKey(models.Model):
    _name = "auth.api.key"
    _inherit = "auth.api.key"

    expiration_date = fields.Datetime(
        help="The key is refused after this date. Leave empty for a key that "
        "does not expire. To rotate a key, create the new one before the "
        "expiration of the old one.",
    )
    expiration_warning_sent = fields.Boolean(
        readonly=True,
        copy=False,
        help="The users in charge were warned that the key is about to expire.",
    )

    @api.model
    def _retrieve_api_key(self, key):
        api_key = super()._retrieve_api_key(key)
        # Not cached: a key expires without any change on the record.
        if api_key._is_expired():
            raise ValidationError(_("The API key is expired"))
        return api_key

    def write(self, vals):
        # A new expiration date needs a new warning.
        if "expiration_date" in vals and "expiration_warning_sent" not in vals:
            vals = dict(vals, expiration_warning_sent=False)
        return super().write(vals)

    def _is_expired(self):
        """Tell if the key is past its expiration date."""
        self.ensure_one()
        return bool(
            self.expiration_date and self.expiration_date < fields.Datetime.now()
        )

    @api.model
    def _get_expiration_warning_users(self):
        """Return the users to warn: the members of the configured group."""
        icp = self.env["ir.config_parameter"].sudo()
        group_id = int(icp.get_param(NOTIFY_GROUP_PARAM) or 0)
        group = self.env["res.groups"].browse(group_id).exists()
        group = group or self.env.ref("base.group_system")
        return group.users.filtered(lambda user: user.active and not user.share)

    @api.model
    def _get_expiration_warning_days(self):
        """Return how many days before the expiration the users are warned.

        Zero (or less) disables the warnings.
        """
        icp = self.env["ir.config_parameter"].sudo()
        return int(icp.get_param(WARNING_DAYS_PARAM) or 0)

    @api.model
    def _cron_warn_expiring_keys(self):
        """Warn the users in charge, once, of all the keys about to expire."""
        warning_days = self._get_expiration_warning_days()
        if warning_days <= 0:
            return
        now = fields.Datetime.now()
        limit = now + timedelta(days=warning_days)
        api_keys = self.search(
            [
                ("expiration_date", ">", now),
                ("expiration_date", "<=", limit),
                ("expiration_warning_sent", "=", False),
            ]
        )
        if not api_keys:
            return
        users = self._get_expiration_warning_users()
        if not users:
            _logger.warning(
                "No user to warn about the API keys about to expire: %s",
                ", ".join(api_keys.mapped("name")),
            )
            return
        warned = False
        for user in users:
            if not api_keys.with_user(user).has_access("read"):
                _logger.warning(
                    "User %s cannot read the API keys: "
                    "not warned of their expiration",
                    user.login,
                )
                continue
            api_keys._schedule_expiration_activity(user)
            warned = True
        # Keys nobody could be warned about are retried by the next run.
        if warned:
            api_keys.expiration_warning_sent = True

    def _schedule_expiration_activity(self, user):
        """Schedule one To Do for ``user`` listing all the keys (``self``).

        It is set on the contact of the user, as the keys are many.
        """
        api_keys = self.sorted("expiration_date")
        items = Markup("").join(
            Markup("<li>%s</li>")
            % _(
                "%(name)s (user %(user)s): %(date)s",
                name=api_key.name,
                user=api_key.user_id.display_name,
                date=fields.Datetime.to_string(api_key.expiration_date),
            )
            for api_key in api_keys
        )
        note = Markup('<p>%s</p><ul>%s</ul><p><a href="%s">%s</a></p>') % (
            _(
                "These API keys are about to expire. Replace them before, "
                "or their callers will be refused."
            ),
            items,
            "/odoo/action-auth_api_key.auth_api_key_act_window",
            _("Open the API keys"),
        )
        user.partner_id.activity_schedule(
            "mail.mail_activity_data_todo",
            date_deadline=api_keys[0].expiration_date.date(),
            summary=_("API keys about to expire"),
            note=note,
            user_id=user.id,
        )
