# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

UNINSTALL_MODULES_LIST = [
    # Here we need to list:
    # all modules installed in previous version of odoo,
    # but we don't want to keep.
    # ===> Modules core/enterprise we don't want
    # ===> Modules OCA we don't want
    # ===> Specific modules we don't want
    # ===> OCA modules not available yet, but we want
    # OCA/example-1
    # OCA/example-2
    # ===> Specific modules not migrated yet, but we want
    # ===> OCA modules not available yet, but we don't know if we want
    # OCA/example-1
    # OCA/example-2
    # ===> Specific modules not migrated yet, but we don't know if we want
    # odoo-enterprise-addons
    'sale_subscription_date_extension',
    'sale_subscription_closing_delay',
    'sale_subscription_recurring_next_date_advance',
    'sale_subscription_coupon',
    'sale_subscription_to_close',
    'sale_subscription_to_close_next_date_advance',
    # OCA/sale-workflow
    'sale_automatic_workflow',
    'sale_automatic_workflow_payment_mode',
    # OCA/account-reconcile
    'account_reconcile_model_strict_match_amount',
    # OCA/account-financial-tools
    'account_chart_update',
    # OCA/bank-statement-import
    'account_bank_statement_import_camt_oca',
    'account_bank_statement_import_oca_camt54',
    # OCA/bank-payment
    'account_payment_sale',
    'account_payment_mode',
    'account_payment_partner',
    # OCA/connector
    'connector',
    'component',
    'component_event',
    # OCA/odoo-cloud-platform
    'monitoring_status',
    'session_redis',
    'cloud_platform',
    'attachment_azure',
    'base_attachment_object_storage',
    # OCA/partner-contact
    'partner_firstname',
    # OCA/queue
    'queue_job_cron',
    # OCA/reporting-engine
    'report_wkhtmltopdf_param',
    # OCA/rest-framework
    'base_rest',
    # OCA/server-auth
    'auth_api_key',
    # OCA/server-env
    'server_environment_ir_config_parameter',
    # OCA/l10n-switzerland
    'l10n_ch_qr_no_amount',
    # local-src
    'camptocamp_tools',
    'sale_subscription_invoice_cancel',
    'schweizmobil_account',
    'schweizmobil_account_bank_statement_import',
    'schweizmobil_base',
    'schweizmobil_report',
    'schweizmobil_sale_subscription',
    'schweizmobil_sale_subscription_renewal',
    'wim_connector',
    'wim_queue',
    'wim_rest',
]

TABLES_TO_PRESERVE = [
    # List of table names:
    # "project_project",
]
COLUMNS_TO_PRESERVE = {
    # Dict with table names as keys and list of column names as values:
    # "project_project": ["name", "user_id"],
    "res_users": ["totp_secret"],
    "res_partner": ["signup_token"],
}
MODELS_TO_PRESERVE = [
    # List of model names:
    # "project.project",
]
FIELDS_TO_PRESERVE = {
    # Dict with model names as keys and list of column names as values:
    # "project.project": ["name", "user_id"],
    "res.users": ["totp_secret"],
    "res.partner": ["signup_token"],
}
