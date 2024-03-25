# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

import anthem

# NOTE: This package aims to host all migration scripts related to the
# Odoo+Enterprise standard addons.
# Normally Odoo SA should handle everything during their migration process, but
# it happens that some data could still need some adjustments.

# NOTE: this is an example, to uncomment/update
# from .base import pre as pre_base
# from .stock import post as post_stock


@anthem.log
def pre(ctx):
    # pre_base(ctx)
    pass


@anthem.log
def post(ctx):
    # post_stock(ctx)
    pass
