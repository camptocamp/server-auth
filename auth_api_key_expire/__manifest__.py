# Copyright 2026 Camptocamp SA
# @author Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "Auth API key expiration",
    "summary": "Expiration date for API keys, with a warning before they expire",
    "version": "18.0.1.0.0",
    "license": "LGPL-3",
    "development_status": "Beta",
    "author": "Camptocamp, Odoo Community Association (OCA)",
    "maintainers": ["simahawk"],
    "website": "https://github.com/OCA/server-auth",
    "depends": ["auth_api_key", "mail"],
    "data": [
        "data/ir_config_parameter.xml",
        "data/ir_cron.xml",
        "views/auth_api_key.xml",
        "views/res_config_settings.xml",
    ],
}
