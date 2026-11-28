# Copyright 2026 Camptocamp SA
# @author Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import SUPERUSER_ID, api

from odoo.addons.auth_api_key.models.auth_api_key import HASH_KEYS_PARAM


def migrate(cr, version):
    """Keep the keys stored in plain text on existing databases.

    Hashing keys is the default for new databases, but code relying on
    reading the keys would break on upgrade: it is up to administrators to
    enable it in the settings, which also hashes the existing keys.
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    if env["auth.api.key"].with_context(active_test=False).search_count([]):
        env["ir.config_parameter"].set_param(HASH_KEYS_PARAM, "False")
