# How to build a migration project

A specific entrypoint has been developed to allow us to launch
the migration of the database:
> odoo/bin/migrate-db

This script launch the marabunta migration to the new version.

In this case, the `marabunta_version` table is removed to clean
the old version installed on previous odoo version.

This entry point can be launched like this:

> docker-compose run --rm -e DB_NAME=odoodb migrate-db migrate-db

N.B: About the database migration on integration/production environment,
we have a dedicated service to launch it.

See: https://github.com/camptocamp/business-cloud-template


# For developpers

The `migrate-db` entrypoint is calling differents commands to
perform the migration in several steps, each of them can be called individually:

- `odoo/bin/migrate-db-core` (+ `odoo/songs/migration_db/migration_core.yml`): perform the upgrade of all standard+enterprise addons by removing everything else from the `ADDONS_PATH`
- `odoo/bin/migrate-db-external` (+ `odoo/songs/migration_db/migration_external.yml`): perform the upgrade of all external addons (OCA etc) by removing `odoo/local-src/` from the `ADDONS_PATH`
- `odoo/bin/migrate-db-local` (+ `odoo/songs/migration_db/migration_local.yml`): perform the upgrade of all local/specific addons
- `odoo/bin/migrate-db-cleanup` (+ `odoo/songs/migration_db/migration_cleanup.yml`): uninstall unwanted or not yet migrated addons and cleanup the database

Each script is able to create a database snapshot when the migration is
successful and if we set the environment variable `MAKE_DB_SNAPSHOT`.
These snapshots can then be shared between people in order to work in parallel
on the migration of modules, without restarting the process from the beginning,
allowing quick development iteration.

How to use them:

- `docker-compose run --rm -e DB_NAME=odoodb -e MAKE_DB_SNAPSHOT=1 migrate-db migrate-db-core`
- `docker-compose run --rm -e DB_NAME=odoodb -e MAKE_DB_SNAPSHOT=1 migrate-db migrate-db-external`
- `docker-compose run --rm -e DB_NAME=odoodb -e MAKE_DB_SNAPSHOT=1 migrate-db migrate-db-local`
- `docker-compose run --rm -e DB_NAME=odoodb -e MAKE_DB_SNAPSHOT=1 migrate-db migrate-db-cleanup`

## Important notice

As we use two ways for modules uninstallation, it is important to run your `migrate-db` in a `dev` mode while you develop (see your `docker-compose.yml` or `docker-compose.override.yml`).

To explain furter, here's how the uninstallation works :
 - In `dev` mode, we use a per single module uninstallation to ensure there is no issue for each one independently.
 - In `int` or `prod` mode, we use a batch module uninstallation that speeds up the process by uninstalling all the modules at once (but can avoid to see some issues during the process. Odoo doesn't throw any errors when a dependency of the current module to uninstall is not met or invalid)


## Fake a migration in integration mode locally

Sometimes we need to launch a migration in integration mode to see how the
new behaviors/scripts could affect the database, or migrate a database that
can't be done on the platform (by keeping attachments, passwords, etc).
To do so, you will need to inactivate all platform checks that fails
systematically, even filestore's ones (impossible access outside the platform).

For this you need to specify a file docker-compose.override.yml at the root of
your project including this:

```
# Root file for the dev composition.
#
# This contains the common configuration for all developers
#
# You can create a 'docker-compose.override.yml' to customize it according
# to your needs it will automatically be applied on top of this
# file when the option '-f' of docker-compose is not used

version: '2'
services:

 migrate-db:
   environment:
     RUNNING_ENV: integration
     ODOO_CLOUD_PLATFORM_UNSAFE: 1  # Deactivate platform check
     DISABLE_ATTACHMENT_STORAGE: 1  # Deactivate filestore storage access
     # Useful if you need to boost odoo locally
     # LIMIT_MEMORY_SOFT: 4294967296
     # LIMIT_MEMORY_HARD: 7368709120

# Useful if you need to boost your db locally
#  db:
#    command: >-
#      -c shared_buffers=2048MB
#      -c maintenance_work_mem=2048MB
#      -c wal_buffers=32MB
#      -c effective_cache_size=4096MB
#      -c max_locks_per_transaction=1000
#      -c max_worker_processes=2
```
