# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
import requests

from odoo import fields, models


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

    def get_api_client(self):
        session = requests.Session()
        session.headers['Content-Type'] = 'application/json'
        session.headers['Accept'] = 'application/json'
        return session
