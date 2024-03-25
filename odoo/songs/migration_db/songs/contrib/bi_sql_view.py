# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

import anthem
from psycopg2 import sql


@anthem.log
def disable_all_bi_sql_views(ctx):
    """Disable all BI SQL Views to ease the 'cleanup' migration step.

    Some fields cannot be removed if they are referenced by such views.
    """
    # NOTE: all of this is done in pure SQL as we could not have the
    # 'bi_sql_view' addon available in the targeted version when we start
    # the migration project. We could also remove this addon so better to not
    # depend on it to cleanup the DB.

    # Reset all BI SQL views to 'draft'
    bi_sql_view_query = "UPDATE bi_sql_view SET state='draft'"
    ctx.env.cr.execute(bi_sql_view_query)
    # Remove all tables
    # NOTE: Odoo S.A. DB migration changes some views into real tables
    table_query = """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_name ILIKE 'x_bi_sql_view_%'
        AND table_type = 'BASE TABLE'
    """
    ctx.env.cr.execute(table_query)
    rows = ctx.env.cr.fetchall()
    for row in rows:
        table_name = row[0]
        ctx.env.cr.execute(
            sql.SQL("DROP TABLE IF EXISTS {};").format(sql.Identifier(table_name))
        )
    # Remove views
    view_query = """
        SELECT table_name
        FROM information_schema.views
        WHERE table_name ILIKE 'x_bi_sql_view_%'
    """
    ctx.env.cr.execute(view_query)
    rows = ctx.env.cr.fetchall()
    for row in rows:
        view_name = row[0]
        ctx.env.cr.execute(
            sql.SQL("DROP VIEW IF EXISTS {};").format(sql.Identifier(view_name))
        )
    # Remove materialized views
    view_query = """
        SELECT matviewname
        FROM pg_matviews
        WHERE matviewname ILIKE 'x_bi_sql_view_%'
    """
    ctx.env.cr.execute(view_query)
    rows = ctx.env.cr.fetchall()
    for row in rows:
        view_name = row[0]
        ctx.env.cr.execute(
            sql.SQL("DROP MATERIALIZED VIEW IF EXISTS {};").format(
                sql.Identifier(view_name)
            )
        )
    # Remove models
    models_query = """
        DELETE FROM ir_model WHERE model ILIKE 'x_bi_sql_view.%'
    """
    ctx.env.cr.execute(models_query)


@anthem.log
def pre(ctx):
    disable_all_bi_sql_views(ctx)
