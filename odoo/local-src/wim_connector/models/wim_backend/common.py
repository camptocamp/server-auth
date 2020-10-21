# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
import requests

from odoo import _, api, exceptions, fields, models


class WIMBackend(models.Model):
    _name = 'wim.backend'
    _description = 'WIM Backend'
    _inherit = 'connector.backend'

    uri = fields.Char(string='WIM URI', required=True)
    name = fields.Char(required=True)
    state = fields.Selection(
        selection=[('setup', 'Setup'), ('connected', 'Connected')],
        default='setup',
        required=True,
        readonly=True,
    )
    sale_order_template_id = fields.Many2one(
        "sale.order.template", ondelete="restrict"
    )
    sale_workflow_process_id = fields.Many2one(
        "sale.workflow.process", ondelete="restrict"
    )

    def get_api_client(self):
        session = requests.Session()
        session.headers['Content-Type'] = 'application/json'
        session.headers['Accept'] = 'application/json'
        return session

    @api.model
    def get_singleton(self):
        return self.env.ref('wim_connector.wim_backend_config')

    @api.model
    def create(self, vals):
        existing = self.search_count([])
        if existing:
            raise exceptions.UserError(
                _("Only 1 backend configuration allowed.")
            )
        return super().create(vals)
