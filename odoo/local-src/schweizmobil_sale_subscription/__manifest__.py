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
        # enterprise
        # TODO: extract this dependency in another module, AGPL not compatible with OPL
        "account_followup",
        # oca/sale-workflow
        "sale_automatic_workflow_payment_mode",
        # odoo/local-src
        "schweizmobil_base",
        # odoo-enterprise-addons
        "sale_subscription_date_extension",
        "sale_subscription_closing_delay",
        "sale_subscription_recurring_next_date_advance",
        "sale_subscription_coupon",
        "sale_subscription_to_close",
        # oca/queue
        "queue_job"
    ],
    "data": [
        "data/ir_cron.xml",
        "data/ir_config_parameter.xml",
        "data/ir_filters.xml",
        "data/account_payment_mode.xml",
        "data/account_payment_term.xml",
        "data/account_followup_followup_line.xml",
        "data/sale_subscription_close_reason.xml",
        "data/sale_subscription_template.xml",
        "data/product_product.xml",
        "data/sale_order_template.xml",
        "data/sale_order_template_line.xml",
        "data/sale_coupon_program.xml",
        # views
        "views/sale_order.xml",
        "views/account_move.xml",
        "views/sale_subscription.xml",
        "wizard/account_move_to_draft.xml",
    ],
    'external_dependencies': {
        'python': ['paramiko'],
    }
}
