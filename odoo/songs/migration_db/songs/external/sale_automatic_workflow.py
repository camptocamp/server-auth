# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

import anthem
from openupgradelib import openupgrade


@anthem.log
def pre(ctx):
    pre_14_0_1_3_0(ctx)


@anthem.log
def pre_14_0_1_3_0(ctx):
    # Copy of pre-migration script written for 14.0.1.3.0 version
    openupgrade.rename_xmlids(
        ctx.env.cr,
        [
            (
                "sale_automatic_workflow_payment_mode.automatic_workflow_payment_filter",
                "sale_automatic_workflow.automatic_workflow_payment_filter",
            ),
        ],
    )
