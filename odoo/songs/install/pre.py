# Copyright 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import os
from base64 import b64encode

import anthem

MAIN_LANG = "fr_FR"
OPT_LANG = ['fr_CH', 'it_IT', 'en_US']
ALL_LANG = [MAIN_LANG] + OPT_LANG


@anthem.log
def setup_company(ctx):
    """Setup company"""
    # load logo on company
    logo_path = os.path.join(ctx.options.odoo_data_path, 'images/company_main_logo.png')
    with open(logo_path, 'rb') as logo_file:
        logo_content = logo_file.read()
    b64_logo = b64encode(logo_content)

    values = {
        'name': "Schweiz Mobil Subscriptions",
        'street': "",
        'zip': "",
        'city': "",
        'country_id': ctx.env.ref('base.ch').id,
        'phone': "+41 00 000 00 00",
        'currency_id': ctx.env.ref('base.CHF').id,
        'email': "contact@schweizmobil-subs.ch",
        'website': "http://www.schweizmobil-subs.ch",
        'vat': "VAT",
        'logo': b64_logo,
    }
    ctx.env.ref('base.main_company').write(values)


@anthem.log
def setup_language(ctx):
    """Installing language and configuring locale formatting"""
    for code in ALL_LANG:
        ctx.env['base.language.install'].create({'lang': code}).lang_install()
    # TODO check your date format
    ctx.env['res.lang'].search([]).write(
        {'grouping': [3, 0], 'date_format': '%d/%m/%Y'}
    )


@anthem.log
def set_default_partner_language(ctx):
    """Define default partner language"""
    Default = ctx.env['ir.default']
    Default.set('res.partner', 'lang', MAIN_LANG, condition=False)


@anthem.log
def admin_user_password(ctx):
    """Changing admin password"""
    # /!\ Future devs if you change the hash placeholder please change too
    # the hooks post_gen_project in odoo-template
    # TODO: default admin password, must be changed.
    # the password placeholder will be replaced by the cookiecutter hook.
    # You'll find the new password on Lastpass with the following name:
    # [odoo-test] schweizmobil-subs test admin user
    # In the lastpass directory: Shared-C2C-Odoo-External
    # To get an encrypted password:
    # $ docker-compose run --rm odoo python3 -c \
    # "from passlib.context import CryptContext; \
    #  print(CryptContext(['pbkdf2_sha512']).encrypt('my_password'))"
    if os.environ.get('RUNNING_ENV') == 'dev':
        ctx.log_line('Not changing password for dev RUNNING_ENV')
        return
    # fmt: off
    ctx.env['res.users']._set_encrypted_password(
        ctx.env.ref('base.user_admin').id, '$pbkdf2-sha512$25000$gRBibO393xujdE6ptXaudQ$lWAUiv6ESMsmtGl7g3/bQr3dat16VtRnIuYtnu4utiPTGumVnBOy1E3eRVtCtz8DqgDOWr7XBjsunMTqWeJwOA'
    )
    # fmt: on


@anthem.log
def main(ctx):
    """Main: creating base config"""
    setup_company(ctx)
    # install only on pre V16 language
    admin_user_password(ctx)
