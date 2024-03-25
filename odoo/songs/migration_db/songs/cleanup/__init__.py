# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

import anthem

# NOTE: This package aims to host all migration scripts related to the cleanup
# of the database. Some data could block this process for technical reasons,
# so here we are able to handle these corner cases.

# NOTE: this is an example, to uncomment/update
# from ..contrib.bi_sql_view import pre as pre_bi_sql_view
# from .my_addon import post as post_my_addon


@anthem.log
def pre(ctx):
    # pre_bi_sql_view(ctx)
    pass


@anthem.log
def post(ctx):
    # post_my_addon(ctx)
    pass
