# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

import anthem
from openupgradelib import openupgrade


@anthem.log
def move_data_from_old_modules(ctx):
    openupgrade.update_module_names(
        ctx.env.cr,
        [
            (
                "schweizmobil_sale_subscription_renewal",
                "schweizmobil_subs_sale_subscription_renewal",
            ),
        ],
        merge_modules=True,
    )


@anthem.log
def pre(ctx):
    move_data_from_old_modules(ctx)
