# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class ResUsersRole(models.Model):
    _inherit = 'res.users.role'

    user_role_code = fields.Char(
        string='HTTP header code'
    )
