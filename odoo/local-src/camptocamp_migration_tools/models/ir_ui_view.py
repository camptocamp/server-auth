# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)


from odoo import fields, models


class IrUiView(models.Model):
    _inherit = "ir.ui.view"

    active_backup = fields.Boolean(
        string="Active (backup)",
        related="active",
        store=True,
        help=(
            "Store the value of 'active' field to help on the migration.\n"
            "Odoo S.A. disables views that can't be applied during their "
            "database migration process, and we need to restore the previous "
            "values at the end of our own migration."
        ),
    )
