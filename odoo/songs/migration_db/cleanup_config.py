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
    # ===> Modules unavailable not installed, but we still have metadata
    'account_payment_sale',
    'schweizmobil_base',
    'account_payment_mode',
    'sale_automatic_workflow',
    'partner_firstname',
    'sale_subscription_closing_delay',
    'sale_subscription_recurring_next_date_advance',
    'camptocamp_tools',
    'sale_automatic_workflow_payment_mode',
    'auth_api_key',
    'server_environment_ir_config_parameter',
    'schweizmobil_sale_subscription',
    'sale_subscription_date_extension',
    'queue_job_cron',
    'sale_subscription_to_close',
    'web_environment_ribbon',
    'wim_queue',
    'connector',
    'server_environment',
    'account_reconcile_model_strict_match_amount',
    'schweizmobil_sale_subscription_renewal',
    'mail_environment',
    'account_bank_statement_import_camt_oca',
    'account_bank_statement_import_oca_camt54',
    'sale_subscription_to_close_next_date_advance',
    'logging_json',
    'component_event',
    'monitoring_status',
    'account_payment_partner',
    'session_redis',
    'cloud_platform',
    'attachment_azure',
    'account_chart_update',
    'wim_rest',
    'base_technical_features',
    'schweizmobil_report',
    'sale_subscription_coupon',
    'wim_connector',
    'schweizmobil_account',
    'l10n_ch_qr_no_amount',
    'cloud_platform_azure',
    'report_wkhtmltopdf_param',
    'schweizmobil_account_bank_statement_import',
    'sale_subscription_invoice_cancel',
    'base_attachment_object_storage',
    'component',
    'base_rest',
    'monitoring_prometheus',
    'queue_job',
]

TABLES_TO_PRESERVE = [
    # List of table names:
    # "project_project",
]
COLUMNS_TO_PRESERVE = {
    # Dict with table names as keys and list of column names as values:
    # "project_project": ["name", "user_id"],
}
MODELS_TO_PRESERVE = [
    # List of model names:
    # "project.project",
]
FIELDS_TO_PRESERVE = {
    # Dict with model names as keys and list of column names as values:
    # "project.project": ["name", "user_id"],
}
