# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
{
    "name": "WIM Connector",
    "summary": "Connector between Odoo and WIM",
    "version": "13.0.1.0.0",
    "category": "Uncategorized",
    "author": "Camptocamp",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "auth_api_key",
        "connector",
    ],
    "data": [
        "data/res_users.xml",
    ],
}
