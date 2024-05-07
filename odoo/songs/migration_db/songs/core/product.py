# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

import anthem


@anthem.log
def post(ctx):
    archive_product_pricelists(ctx)


@anthem.log
def archive_product_pricelists(ctx):
    ctx.env['product.pricelist'].sudo().search([]).action_archive()
