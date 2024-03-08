# Migration project

The whole stack for migrations is now moved to two repositories:
  - migration tools: odoo-upgrade-tools
  - base migration image: odoo-upgrade-service

## Odoo-upgrade-tools

`odoo-upgrade-tools` is to bootstrap a new migration project (by adding `migrate-db` + a new Docker image which will use `migrate-db` as entrypoint, usable by the cloud platform).

[Camptocamp Odoo-upgrade-tools](https://github.com/camptocamp/odoo-upgrade-tools)



## Odoo-upgrade-service by Camptocamp SA

`odoo-upgrade-service` is a service integrated with _OneRing_ to trigger the full migration on the cloud platform, from a production dump to the target version restored on a given environment (lab/int/prod). It will use the [Odoo S.A. Upgrade Service](https://upgrade.odoo.com/), and the project migration Docker image created by `odoo-upgrade-tools` above.

[Camptocamp Odoo-upgrade-service](https://github.com/camptocamp/odoo-upgrade-service/)

WARNING: this is not operational yet
