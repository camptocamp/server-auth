# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
{
    'name': 'WIM Base',
    'version': '17.0.1.0.0',
    'author': 'Camptocamp',
    'license': 'AGPL-3',
    'category': 'Others',
    'depends': [
        # odoo/src
        "base",
        "partner_firstname",
    ],
    'website': 'http://www.camptocamp.com',
    'data': [
        # views
        "views/res_partner.xml",
    ],
    'installable': True,
}
