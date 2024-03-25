# Quick overview of the current procedure of server update for migration

## Before go-live

When we migrate inbetween major versions of odoo, we often need to update the configuration.
The configuration update of prod stack should be done before the day of the go-live.
Points that could need an update:
  - image tag for the deploy
  - memory
  - number of workers
  - load command

## Go-Live

**WARNING, the operation of restoring the database can only be done by power-users. If you're not one of them you will
not be able to do the go-live**

### On the platform
- Scale down prod `replicaCount: 0`
- Copy prod to previous version lab (if required)
- Send a db for migration to Odoo

### locally on your laptop with the version you want to deploy
- Update the docker-compose.override.yml file with "Fake migration settings". Pay attention at the `RUNNING_ENV`

```
version: '2'
services:
  migrate-db:
    environment:
      RUNNING_ENV: prod
      ODOO_CLOUD_PLATFORM_UNSAFE: 1
      DISABLE_ATTACHMENT_STORAGE: 1
      LIMIT_MEMORY_SOFT: 4294967296
      LIMIT_MEMORY_HARD: 7368709120
      AZURE_STORAGE_ACCOUNT_NAME: XXXXX
      AZURE_STORAGE_ACCOUNT_URL: XXXXX
      AZURE_STORAGE_ACCOUNT_KEY: XXXXX

  db:
    command: >-
      -c shared_buffers=2048MB
      -c maintenance_work_mem=2048MB
      -c wal_buffers=32MB
      -c effective_cache_size=4096MB
      -c max_locks_per_transaction=1000
      -c max_worker_processes=2
```

- Once the db upgrade is finished on upgrade.odoo.com service, retrieve the database and restore it locally
- Launch the migration locally with a command like `docker-compose run --rm -e DB_NAME=odoodb migrate-db migrate-db`
- Once the migration is finished locally we need to have a dump locally `pg_dump -h localhost -p {port} -U odoo -Fc -d odoodb -f {customer-migrated-locally-YYYY-MM-DD}.pg`

### On the platform

**WARNING** You need to be a power-user to restore the database

We have now a database that is migrated locally. We want to restore it and relaunch the server.

- Connect to the global console
- Kill all pending connections to the database
```
-- kill all connection
 SELECT pg_terminate_backend(pg_stat_activity.pid)
FROM pg_stat_activity
WHERE pg_stat_activity.datname = 'REPLACE_ME_WITH_DB_NAME'
  AND pid <> pg_backend_pid();
```

- Restore the dump (sample command, for the mtsmte project. Please update it accordingly)
https://github.com/camptocamp/bs-cloudplatform-doc/blob/main/cheatsheet.md
cat DB_LOCAL_DUMP_MIGRATED.pg | kubectl --kubeconfig ~/.kube/odoo_ch_prod exec -n bs-odoo-CLIENT-prod -ti psql-console-7878cf6445-l5dhd -- pg_restore -d REPLACE_ME_WITH_DB_NAME

- Once done you can restart the project `replicaCount: 2`
  - restore the previous value, this is a sample command

### Potential known issues

- Icons are not displayed
  - log into the odoo-shell of the instance and run the following

```
odoo shell --no-xmlrpc

menus = env['ir.ui.menu'].search([('web_icon', '!=', False)])
for menu in menus:
    menu.web_icon = menu.web_icon

env['ir.ui.menu'].clear_caches()
env.cr.commit()
```
