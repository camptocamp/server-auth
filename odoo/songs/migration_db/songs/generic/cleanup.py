# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import uuid

import anthem
import psycopg2
from openupgradelib import openupgrade

from odoo.exceptions import UserError
from odoo.modules.module import load_information_from_description_file

from ...cleanup_config import (
    COLUMNS_TO_PRESERVE,
    FIELDS_TO_PRESERVE,
    MODELS_TO_PRESERVE,
    TABLES_TO_PRESERVE,
)

TABLES_TO_PRESERVE.extend(
    [
        # The marabunta_version table must never be deleted
        "marabunta_version",
        # Required by postgis, no effect when postgis is not installed
        "spatial_ref_sys",
    ]
)
COLUMNS_TO_PRESERVE.update(
    {
        # Due to a bug on database_cleanup module in v12,
        # the column password of res.users is removed.
        # See comments: https://github.com/OCA/server-tools/pull/1408
        # So we just ignore that column here.
        "res_users": ["password"],
    }
)


@anthem.log
def clean_models_from_uninstalled_modules(ctx):
    """Clean models from uninstalled modules."""
    try:
        purge_models = ctx.env["cleanup.purge.wizard.model"].create({})
    except UserError as e:
        ctx.log_line("No models to purge: '{}'".format(str(e)))
        return
    try:
        lines = purge_models.purge_line_ids
        if MODELS_TO_PRESERVE:
            lines = lines.filtered(lambda ln: ln.name not in MODELS_TO_PRESERVE)
        ctx.log_line(
            "Start purging the following models: {}".format(lines.mapped("name"))
        )
        lines_in_error = lines.browse()
        # As a model could depend on another one, postpone its purge until we purged
        # as many models as possible. Stop the loop as soon an error occurs again
        # while purging an already processed model.
        while lines:
            line = lines[:1]
            try:
                ctx.log_line("Try to purge: %s" % line.name)
                with ctx.env.cr.savepoint():
                    line.purge()
            except Exception:
                if line in lines_in_error:
                    # Entering in an infinite loop, break here with an error
                    ctx.log_line(
                        "Some models haven't been purged, check the logs above."
                    )
                    break
                # Postpone the line to purge it at the end
                lines -= line
                lines += line
                # Flag it as errored
                lines_in_error |= line
            else:
                lines -= line
                lines_in_error -= line
    except UserError as e:
        ctx.log_line("Cleanup resulted in error: '{}'".format(str(e)))


@anthem.log
def clean_columns_and_fields_from_uninstalled_modules(ctx):
    """Clean columns/fields from uninstalled modules."""
    ctx.log_line("Start purging columns")
    try:
        purge_columns = ctx.env["cleanup.purge.wizard.column"].create({})
        purge_column_lines = purge_columns.purge_line_ids
        if TABLES_TO_PRESERVE:
            purge_column_lines = purge_column_lines.filtered(
                lambda ln: ctx.env[ln.model_id.model]._table not in TABLES_TO_PRESERVE
            )
        if MODELS_TO_PRESERVE:
            purge_column_lines = purge_column_lines.filtered(
                lambda ln: ln.model_id.model not in MODELS_TO_PRESERVE
            )
        if COLUMNS_TO_PRESERVE:
            purge_column_lines = purge_column_lines.filtered(
                lambda ln: ln.name
                not in COLUMNS_TO_PRESERVE.get(ctx.env[ln.model_id.model]._table, [])
            )
        if FIELDS_TO_PRESERVE:
            purge_column_lines = purge_column_lines.filtered(
                lambda ln: ln.name not in FIELDS_TO_PRESERVE.get(ln.model_id.model, [])
            )
        for purge_column_line in purge_column_lines:
            # Sometimes we cannot control the dependencies of a SQL object
            # against a column that has to be purged: e.g. SQL views created
            # by standard addons and depending on every columns of a given
            # table (even custom columns).
            # Better to not block the migration in such cases.
            try:
                # Create our own savepoint without 'cr.savepoint()' helper to
                # avoid the call to 'RELEASE SAVEPOINT'. Indeed as 'purge()'
                # method used below is calling 'cr.commit()', the current
                # savepoint is automatically released if everything went well,
                # so we only need to handle the ROLLBACK.
                name = uuid.uuid1().hex
                ctx.env.cr.execute('SAVEPOINT "%s"' % name)
                ctx.log_line(
                    "Try to purge column: %s.%s"
                    % (
                        ctx.env[purge_column_line.model_id.model]._table,
                        purge_column_line.name,
                    )
                )
                purge_column_line.purge()
            except psycopg2.errors.DependentObjectsStillExist as e:
                ctx.log_line("Purge error: '{}'".format(str(e)))
                ctx.env.cr.execute('ROLLBACK TO SAVEPOINT "%s"' % name)
    except UserError as e:
        ctx.log_line("Cleanup resulted in error: '{}'".format(str(e)))


def clean_db_tables(ctx, count_clean):
    """Clean tables from uninstalled modules."""
    is_table_cleaned = True
    ctx.log_line("Start purging tables attempt n° {}".format(count_clean))
    try:
        purge_tables = ctx.env["cleanup.purge.wizard.table"].create({})
        purge_table_lines = purge_tables.purge_line_ids
        if TABLES_TO_PRESERVE:
            purge_table_lines = purge_table_lines.filtered(
                lambda ln: ln.name not in TABLES_TO_PRESERVE
            )
        for purge_table_line in purge_table_lines:
            ctx.log_line("Try to purge table: %s" % purge_table_line.name)
            try:
                with ctx.env.cr.savepoint():
                    purge_table_line.purge()
            except Exception:
                is_table_cleaned = False
    except UserError as e:
        ctx.log_line("Cleanup resulted in error: '{}'".format(str(e)))
    return is_table_cleaned


@anthem.log
def clean_models_data_from_uninstalled_modules(ctx):
    """Clean models data from uninstalled modules."""
    ctx.log_line("Start purging datas")
    try:
        purge_datas = ctx.env["cleanup.purge.wizard.data"].create({})
        purge_data_lines = purge_datas.purge_line_ids.filtered(
            # Metadata exported, imported or from setup must not be deleted
            lambda ln: "__export__" not in ln.name
            and "__setup__" not in ln.name
            and "__import__" not in ln.name
        )
        for purge_data_line in purge_data_lines:
            ctx.log_line("Try to purge data: %s" % purge_data_line.name)
            purge_data_line.purge()
    except UserError as e:
        ctx.log_line("Cleanup resulted in error: '{}'".format(str(e)))


@anthem.log
def clean_menus_from_uninstalled_modules(ctx):
    """Clean menus from uninstalled modules."""
    ctx.log_line("Start purging menus")
    try:
        purge_menus = ctx.env["cleanup.purge.wizard.menu"].create({})
        purge_menu_lines = purge_menus.purge_line_ids
        for purge_menu_line in purge_menu_lines:
            ctx.log_line("Try to purge menu: %s" % purge_menu_line.name)
            purge_menu_line.purge()
    except UserError as e:
        ctx.log_line("Cleanup resulted in error: '{}'".format(str(e)))


@anthem.log
def database_cleanup(ctx):
    """Clean database"""

    clean_models_from_uninstalled_modules(ctx)
    clean_columns_and_fields_from_uninstalled_modules(ctx)

    to_clean = True
    count_clean = 0
    while to_clean:
        count_clean += 1
        to_clean = not clean_db_tables(ctx, count_clean)

    clean_models_data_from_uninstalled_modules(ctx)
    clean_menus_from_uninstalled_modules(ctx)


@anthem.log
def clean_unavailable_modules(ctx):
    """Clean unavailable modules

    When we migrate a project,
    we have a lot of modules which became unavailable in the new version.
    This function will clean the module list to delete unavailable modules.
    """
    module_model = ctx.env["ir.module.module"]
    all_modules = module_model.search(
        [
            # Here we need to list:
            # all modules uninstalled we want to migrate
            # to avoid to remove them
            # Example:
            # (
            #     'name',
            #     'not in',
            #     [
            #         'account_asset_management',              # To migrate!
            #     ]
            # )
        ]
    )
    for module in all_modules:
        info = load_information_from_description_file(module.name)
        if not info:
            if module.state in ["uninstalled", "uninstallable"]:
                ctx.log_line("MODULE UNAVAILABLE (will be deleted) : %s" % module.name)
                if ctx.env["ir.model.data"].search([("module", "=", module.name)]):
                    ctx.log_line(
                        "===> CAN'T UNLINK MODULE, WE HAVE METADATA "
                        "(See if we want to migrate or uninstall the module)"
                    )
                else:
                    module.unlink()
            else:
                ctx.log_line(
                    "MODULE UNAVAILABLE BUT BAD STATE : %s (%s)"
                    % (module.name, module.state)
                )

    module_model.update_list()


@anthem.log
def purge_migration_sql_objects(ctx):
    # Clean the SQL objects created earlier in pre-core to handle upgrade of views
    queries = [
        """
        DROP TRIGGER IF EXISTS trigger_enable_views_for_upgraded_addons
        ON ir_module_module;
        """,
        """
        DROP FUNCTION IF EXISTS enable_views_for_upgraded_addons;
        """,
    ]
    for query in queries:
        ctx.env.cr.execute(query)


@anthem.log
def repair_missing_menu_icons(ctx):
    menus = ctx.env["ir.ui.menu"].search([("web_icon", "!=", False)])
    for menu in menus:
        menu.web_icon = menu.web_icon
    ctx.env["ir.ui.menu"].clear_caches()


@anthem.log
def disable_invalid_filters(ctx):
    openupgrade.disable_invalid_filters(ctx.env)


@anthem.log
def cleanup_home_actions_from_users(ctx):
    # Some home actions configured on users doesn't exist anymore and
    # a blank page is rendered once logged.
    # It happens there is no foreign key on the 'res_users.action_id' field
    # (checked on 13.0, 14.0 and 15.0 databases), so if the action is removed
    # during the migration process, a ghost ID remains in this column.
    query = """
        UPDATE res_users
        SET action_id = NULL
        WHERE action_id NOT IN (
            SELECT id FROM ir_actions
        );
    """
    ctx.env.cr.execute(query)


@anthem.log
def post(ctx):
    purge_migration_sql_objects(ctx)
    database_cleanup(ctx)
    clean_unavailable_modules(ctx)
    repair_missing_menu_icons(ctx)
    disable_invalid_filters(ctx)
    cleanup_home_actions_from_users(ctx)
