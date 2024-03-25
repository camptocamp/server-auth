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
