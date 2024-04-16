# Copyright 2024 Camptocamp SA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
{
    'name': 'Schweiz Mobil Subscriptions - Bundle EE',
    'version': '17.0.1.0.0',
    'author': 'Camptocamp',
    'license': 'LGPL-3',
    'category": "Bundle'
    'website': 'http://www.camptocamp.com',
    'depends': [
        # enterprise
        'account_bank_statement_import_camt',
        'account_followup',
        'sale_subscription',
        # camptocamp/odoo-enterprise-addons
        'sale_subscription_to_close',
        'sale_subscription_closing_delay',
        'sale_subscription_invoice_cancel',
        'sale_subscription_next_invoice_date_advance',
        'sale_subscription_to_close_next_date_advance'
    ],
    'installable': True,
    'auto_install': False,
}
