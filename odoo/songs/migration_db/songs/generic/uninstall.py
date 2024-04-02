# Copyright 2019 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
import os
from time import gmtime, strftime

import anthem

from ...cleanup_config import UNINSTALL_MODULES_LIST


@anthem.log
def uninstall_modules(ctx):
    """Uninstall modules"""
    # For development purpose, we uninstall modules one by one to catch
    # any error that could be hidden by a batch-uninstallation. Once things
    # have been stabilized, we allow a batch-uninstallation of modules on
    # non-dev environments to speed up the process.
    #   => Test done with Odoo 15.0 shows for 275 modules to uninstall:
    #    - by batch: 289.435s
    #    - one by one: 441.453s
    #   Uninstalled time decreased by almost 35% in batch.
    batch_uninstall = os.environ.get("RUNNING_ENV") != "dev"
    if UNINSTALL_MODULES_LIST:
        modules = ctx.env["ir.module.module"].search(
            [("name", "in", UNINSTALL_MODULES_LIST)]
        )
        # Odoo add a check to deny uninstall of non-installed module.
        # But in migration context, we want to uninstall module without have an
        # installed status. Because for some modules, we don't have sources.
        # Then we need to force the state to 'installed' or 'to upgrade' to
        # avoid this issue.
        modules.write({"state": "installed"})
        if batch_uninstall:
            ctx.log_line(
                "Try to uninstall all modules : %s" % str([m.name for m in modules])
            )
            modules.button_immediate_uninstall()
        else:
            for module in modules:
                params = (strftime("%Y-%m-%d %H:%M:%S", gmtime()), module.name)
                # If module has been previously uninstalled by a dependency
                # Avoid throwing an Odoo UserError
                if module.state not in ("installed", "to upgrade"):
                    ctx.log_line(
                        "%s Module already uninstalled by a dependency: %s" % params
                    )
                    continue
                ctx.log_line("%s Try to uninstall module: %s" % params)
                try:
                    module.button_immediate_uninstall()
                except Exception as exc:
                    ctx.log_line(exc)
    else:
        ctx.log_line("No modules to uninstall")


@anthem.log
def update_state_for_uninstalled_modules(ctx):
    """Update state for uninstalled modules
    to avoid to install/update them into the build"""
    if UNINSTALL_MODULES_LIST:
        sql = """
            UPDATE
                ir_module_module
            SET
                state = 'uninstalled'
            WHERE
                name IN %s;
        """
        ctx.env.cr.execute(sql, [tuple(UNINSTALL_MODULES_LIST)])
    else:
        ctx.log_line("No modules to uninstall")


@anthem.log
def pre(ctx):
    """PRE: uninstall"""
    update_state_for_uninstalled_modules(ctx)


@anthem.log
def post(ctx):
    """POST: uninstall"""
    uninstall_modules(ctx)
