# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
import anthem


@anthem.log
def update_available_addons(ctx):
    ctx.env["ir.module.module"].update_list()
