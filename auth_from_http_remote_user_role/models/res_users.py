# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import api, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.multi
    def change_roles_user(self, new_roles):
        """ Change the roles of the user """
        self.ensure_one()
        new_roles = set(new_roles)
        existing_roles = set(self.role_ids.ids)
        roles2add = list(new_roles.difference(existing_roles))
        roles2remove = list(existing_roles.difference(new_roles))
        if roles2add:
            triplets = [(0, False, {'role_id': roleid, 'user_id': self.id})
                        for roleid in roles2add]
            self.role_line_ids = triplets
        if roles2remove:
            self.role_line_ids.search([
                ('user_id', '=', self.id),
                ('role_id', 'in', roles2remove)]).unlink()
