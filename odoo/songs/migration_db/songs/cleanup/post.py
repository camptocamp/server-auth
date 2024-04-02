# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

import anthem

from odoo.tools.sql import column_exists, create_column


@anthem.log
def initialize_auth_core_columns(ctx):
    # create columns if not exists for authentication auto installed modules
    if not column_exists(ctx.env.cr, "res_users", "totp_secret"):
        create_column(ctx.env.cr, "res_users", "totp_secret", "varchar")
    if not column_exists(ctx.env.cr, "res_partner", "signup_token"):
        create_column(ctx.env.cr, "res_partner", "signup_token", "varchar")


@anthem.log
def post(ctx):
    initialize_auth_core_columns(ctx)
