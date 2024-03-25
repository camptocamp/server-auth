# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

# NOTE: here are some examples of common 'openupgradelib' functions that will
# help you to migrate data.
# You will find the list of functions available here:
# https://github.com/OCA/openupgradelib/blob/master/openupgradelib/openupgrade.py


import anthem
from openupgradelib import openupgrade


@anthem.log
def migrate_field_x_from_addon1_to_addon2(ctx):
    openupgrade.update_module_moved_fields(
        ctx.env.cr, "res.partner", ["field_x"], "addon1", "addon2"
    )


def migrate_model_x_from_addon1_to_addon2(ctx):
    xmlids_spec = [("addon1.model_x", "addon2.model_x")]
    openupgrade.rename_xmlids(ctx.env.cr, xmlids_spec)


@anthem.log
def rename_model_x(ctx):
    models_spec = [("model_x", "new_model_x")]
    openupgrade.rename_models(ctx.env.cr, models_spec)


@anthem.log
def rename_addon(ctx):
    openupgrade.update_module_names(
        ctx.env.cr, [("old_addon_name", "new_addon_name")], merge_modules=True
    )


@anthem.log
def pre(ctx):
    migrate_field_x_from_addon1_to_addon2(ctx)
    migrate_model_x_from_addon1_to_addon2(ctx)
    rename_model_x(ctx)
    rename_addon(ctx)
