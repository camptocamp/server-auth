# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    'name': 'Schweiz Mobil Subscriptions - Bundle',
    'version': '17.0.1.0.0',
    'author': 'Camptocamp',
    'license': 'AGPL-3',
    'category": "Bundle'
    'website': 'http://www.camptocamp.com',
    'depends': [
        # odoo
        'contacts',
        'l10n_ch',
        'sale_loyalty',
        # oca/bank-payment,
        'account_payment_mode',
        'account_payment_partner',
        'account_payment_sale',
        # oca/connector
        'component',
        'component_event',
        'connector',
        # oca/partner-contact
        'partner_firstname',
        # oca/sale-workflow
        'sale_automatic_workflow',
        'sale_automatic_workflow_payment_mode',
        # oca/server-env
        'mail_environment',
        'server_environment',
        'server_environment_ir_config_parameter',
        # oca/server-ux
        'base_technical_features',
        # oca/queue
        'queue_job',
        'queue_job_cron',
        # oca/web
        'web_environment_ribbon',
        # oca/queue
        'queue_job',
        'queue_job_cron',
        # oca/connector
        'connector',
        'component',
        'component_event',
        # oca/sale-workflow
        'sale_automatic_workflow',
        'sale_automatic_workflow_payment_mode',
        # oca/server-tools
        'database_cleanup',
        # camptocamp/odoo-cloud-platform
        'attachment_azure',
        'monitoring_status',
        'monitoring_prometheus',
        'session_redis',
        'base_attachment_object_storage',
        'logging_json',
        # local-src
        'camptocamp_tools',
        'schweizmobil_subs_base',
    ],
    'installable': True,
    'auto_install': False,
}
