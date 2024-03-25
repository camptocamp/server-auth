# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

import anthem

# NOTE: This package aims to host all migration scripts related to external
# addons like OCA. Generic migration scripts should - of course - be added
# directly in the OCA addons, but we sometimes need to do our own migration
# scripts related to an OCA addon, for instance:
#   - we migrated from one specific addon to an OCA one (need to migrate data)
#   - the new version of an OCA addon has removed a field but we want to preserve
#     it in a specific addon (need to preserve the DB column otherwise it'll get
#     deleted during the upgrade)
#   - apply a specific configuration so the upgrade doesn't crash
#
# The use of 'openupgradelib' Python package could help you to write such
# migration scripts.

# NOTE: this is an example, to uncomment/update
# from .my_addon import pre as pre_my_addon
# from .my_addon import post as post_my_addon


@anthem.log
def pre(ctx):
    # pre_my_addon(ctx)
    pass


@anthem.log
def post(ctx):
    # post_my_addon(ctx)
    pass
