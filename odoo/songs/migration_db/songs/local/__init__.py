# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

import anthem
from .schweizmobil_subs_base import pre as pre_schweizmobil_subs_base

from .schweizmobil_subs_account import pre as pre_schweizmobil_subs_account

# NOTE: This package aims to host all migration scripts related to specific
# addons or customer data that need some adjustments. For instance:
#   - add a specific group on some user accounts
#   - handle the renaming of a specific addon
#   - move fields from one addon to another
#   - update some records (to set a new field, trigger a recompute...)

# The use of 'openupgradelib' Python package could help you to write such
# migration scripts.

# NOTE: this is an example, to uncomment/update
# from .my_addon import pre as pre_my_addon
# from .my_addon import post as post_my_addon


@anthem.log
def pre(ctx):
    # pre_my_addon(ctx)
    pre_schweizmobil_subs_account(ctx)
    pre_schweizmobil_subs_base(ctx)


@anthem.log
def post(ctx):
    # post_my_addon(ctx)
    pass
