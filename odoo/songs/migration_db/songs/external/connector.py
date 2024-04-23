# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

import anthem


@anthem.log
def pre(ctx):
    pre_remove_connector_checkpoint(ctx)


@anthem.log
def pre_remove_connector_checkpoint(ctx):
    query = "DELETE FROM ir_model WHERE model='connector.checkpoint';"
    ctx.env.cr.execute(query)
