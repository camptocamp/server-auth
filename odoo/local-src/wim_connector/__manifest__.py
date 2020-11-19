# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
{
    "name": "WIM Connector",
    "summary": "Connector between Odoo and WIM",
    "version": "13.0.1.0.0",
    "category": "Connector",
    "author": "Camptocamp",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "external_dependencies": {
        "python": ["requests"]
    },
    "depends": [
        "connector",
        # local-src
        "wim_sale",
        "schweizmobil_base",
        "wim_subscription",
        "wim_queue",
        # oca/server-env
        "server_environment",
    ],
    "data": [
        # data
        "data/connector_backend.xml",
        "security/ir.model.access.csv",
        # views
        "views/res_partner.xml",
        "views/sale_subscription.xml",
        "views/wim_backend.xml",
    ],
}
