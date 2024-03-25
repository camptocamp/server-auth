# How to send a database to odoo and share it

When we run migrations we need to send database to odoo for migration.

## Pre-requisites

* celebrimbor access to the project you need to work with. If you don't have it -> ticket to [BGIS](https://jira.camptocamp.com/servicedesk/customer/portal/11)
* celebrimbor-cli installed
* Customer license/contract number - Can be found on:
  * ir.config_parameter in GUI or database `SELECT * from ir_config_parameter where key='database.enterprise_code';`
  * odoo.com
  * the confluence migration page of the project



## Send the database to Odoo

Download locally the database you want to migrate with [celebrimbor-cli](https://github.com/camptocamp/bs-cloudplatform-doc/blob/main/cheatsheet.md#celebrimbor)

Rename it from `DUMP_NAME.pg` -> `DUMP_NAME.dump`

`python <(curl -s https://upgrade.odoo.com/upgrade) test --dump <dump file> -t <target version> -c <customer license>`

/!\ When migration starts, odoo will provide a token that is stored in `/tmp/`
If for some reason your computer restarts during this process, this token will be lost,
and you wont be able to resume the migration.
To avoid this, one should save the generated `/tmp/odoo-upgrade-production-dump_<FINGERPRINT>-<ODOO_VERSION>` file somewhere.
If for whatever reason your computer restarts, just place this file in `/tmp` and the previous migration will be resumed,
when executing the odoo `upgrade` script.

When the migration is finished, you will receive from odoo a zipfile containing:
* an sql file
* a folder containing the filestore
* a migration logfile

Extract the dump from the zipfile and rename it dump.sql -> `{customer_name}-odoo-migrated-YYYYMMDD.sql`

Upload it with [celebrimbor-cli](https://github.com/camptocamp/bs-cloudplatform-doc/blob/main/cheatsheet.md#celebrimbor)

WARNING:

The uploaded file will be stored with the following format:
`{customer_name}-odoo-migrated-YYYYMMDD-HHMMSS.pg.gpg`
