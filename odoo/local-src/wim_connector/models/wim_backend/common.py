# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
import requests

from odoo import _, api, exceptions, fields, models


class WIMBackend(models.Model):
    _name = 'wim.backend'
    _description = 'WIM Backend'
    _inherit = [
        'connector.backend',
        'server.env.techname.mixin',
        'server.env.mixin',
    ]

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
    payment_mode_id = fields.Many2one(
        "account.payment.mode", ondelete="restrict"
    )
    swisspass_promotion_program_id = fields.Many2one(
        "sale.coupon.program", ondelete="restrict"
    )
    user_name = fields.Char(string="User Name")
    user_password = fields.Char(string="User Password")

    @property
    def _server_env_fields(self):
        base_fields = super()._server_env_fields
        backend_fields = {"uri": {}, "user_name": {}, "user_password": {}}
        backend_fields.update(base_fields)
        return backend_fields

    def get_api_client(self):
        session = requests.Session()
        session.headers['Content-Type'] = 'application/json'
        session.headers['Accept'] = 'application/json'
        session.auth = (self.user_name, self.user_password)
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
