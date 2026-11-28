# Copyright 2026 Camptocamp SA
# @author Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    auth_api_key_expire_group_id = fields.Many2one(
        comodel_name="res.groups",
        string="API key expiration: group to warn",
        config_parameter="auth_api_key_expire.notify_group_id",
        help="The members of this group get a To Do when an API key is about "
        "to expire. They need read access to the API keys.",
    )
    auth_api_key_expire_warning_days = fields.Integer(
        string="API key expiration: days before",
        config_parameter="auth_api_key_expire.warning_days",
        default=15,
        help="How many days before its expiration a key is warned about. "
        "0 disables the warnings.",
    )
