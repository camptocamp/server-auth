# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
{
    "name": "Schweizmobil Sale Subscription",
    "summary": "Schweizmobil Sale Subscription specifics",
    "version": "13.0.1.0.0",
    "category": "Uncategorized",
    "author": "Camptocamp",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "l10n_ch",
        "sale",
        "sale_management",
        "sale_coupon",
        "account",
        # oca/sale-workflow
        "sale_automatic_workflow_payment_mode",
        # odoo/local-src
        "schweizmobil_base",
        # odoo-enterprise-addons
        "sale_subscription_date_extension",
        "sale_subscription_closing_delay",
        "sale_subscription_recurring_next_date_advance",
    ],
    "data": [
        "data/account_payment_mode.xml",
        "data/sale.subscription.template.csv",
        "data/product.product.csv",
        "data/sale.order.template.csv",
        "data/sale.order.template.line.csv",
        "data/sale.coupon.program.csv",
        # views
        "views/sale_order.xml",
        "views/account_move.xml",
    ]
}
