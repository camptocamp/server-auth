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
        # oca/server-env
        'mail_environment',
        'server_environment',
        'server_environment_ir_config_parameter',
        # oca/server-ux
        'base_technical_features',
        # oca/web
        'web_environment_ribbon',
        # oca/queue
        'queue_job',
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
    ],
    'installable': True,
    'auto_install': False,
}
