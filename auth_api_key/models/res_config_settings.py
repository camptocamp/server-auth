# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    archived_user_disable_auth_api_key = fields.Boolean(
        related="company_id.archived_user_disable_auth_api_key", readonly=False
    )

    auth_api_key_hash_keys = fields.Boolean(
        string="Store API keys hashed",
        config_parameter="auth_api_key.hash_keys",
        default=True,
        help="Store only a hash of the API keys: a key is readable only when "
        "it is created. Enabling it also hashes the keys already stored.",
    )

    def set_values(self):
        res = super().set_values()
        if self.auth_api_key_hash_keys:
            self.env["auth.api.key"]._hash_plaintext_keys()
        return res
