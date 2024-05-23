# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import fields, models


class WIMBinding(models.AbstractModel):
    """Abstract Model for the Bindings.
    All the models used as bindings between WIM and Odoo
    (``wim.res.partner``, ...) should ``_inherit`` it.
    """

    _name = 'wim.binding'
    _inherit = 'external.binding'
    _description = 'WIM Binding (abstract)'

    # odoo-side id must be declared in concrete model
    # odoo_id = fields.Many2one(...)
    backend_id = fields.Many2one(
        comodel_name='wim.backend',
        string='WIM Backend',
        required=True,
        ondelete='restrict',
    )
    external_id = fields.Char(string='ID on WIM', index=True)

    def export_record(self, fields=None):
        self.ensure_one()
        with self.backend_id.work_on(self._name) as work:
            exporter = work.component(usage='record.exporter')
            return exporter.run(self, fields=fields)
