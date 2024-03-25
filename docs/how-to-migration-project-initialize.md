# How to initialize a migration project

## Initialization steps

### Create the new branch

First step is to create the new branch for the new version.

In the past, the branch was created from master and took the name of the new version.
By example `14.0` for a migration to version 14.

Now, we create a project from scratch and retrieve only the needed material to propose a clean database for the
migration process:

* Use of cookiecutter normally to create a new project with the same parameters than the previous version (see .cookicutter)
    * `cookiecutter git@github.com:camptocamp/odoo-template`
* Then checkout and enter the new branch with the desired new version on this new project (you should have the right remote reporitory to point to but double check it)
    * git checkout -b 14.0
    * git push --set-upstream origin 14.0
    * invoke submodule.init
    * invoke submodule.update
* Then use the tool `odoo-upgrade-tool` here to install all the database migration scripts and configuration
  * see https://github.com/camptocamp/odoo-upgrade-tools for further information
* Then build all the images used in the docker services (not only the odoo one!)
  * `docker-compose build`

! this is a "bare instance".

For next steps:

* Don't commit directly on that new branch, but propose a pull request on it.
* Use different commit for each action to help reviewers understand your changes.

### Retrieve some of the needed configuration from the previous version

While database is sent to Odoo S.A. upgrade platform you can continue with project setup. And also it's a good practice to test if building an empty DB can be done successfully.
* docker-compose build odoo
* docker-compose run --rm -p 8069:8069 odoo odoo --workers=0

Then you need to check and update company info, this is configured at setup step listed in migration.yml
* in `songs/install/pre.py`:
  * Get the admin password (the hash) from previous version to the new one
  * Check that company configuration is same as the previous one
* Copy the old logo to the new project if not changed (ask for the new one if needed)
  * Then commit it as `Update company, logo and password from previous project version`
* Update the `odoo/songs/migration_db/addons_to_uninstall.py` file with the list of all modules that still need to be migrated or to uninstall:
  * Extract the list of modules from the DB migrated by Odoo S.A.:
    - `SELECT name FROM ir_module_module WHERE state='to upgrade';`
  * Remove from this list (if present) the required modules to run Odoo on our Cloud Platform, and make sure these modules are migrated and available in the `$ADDONS_PATH`:
    - `local-src` ones:
      - `camptocamp_website_tools`
      - `camptocamp_tools`
    - `OCA/server-tools`:
      - `database_cleanup`
    - `OCA/server-ux`:
      - `base_technical_features`
    - `OCA/server-env`:
      - `mail_environment`
      - `server_environment`
      - `server_environment_ir_config_parameter`
    - `OCA/web`:
      - `web_environment_ribbon`
    - `camptocamp/odoo-cloud-platform`:
      - `attachment_azure`
      - `base_attachment_object_storage`
      - `cloud_platform`
      - `cloud_platform_azure`
      - `logging_json`
      - `monitoring_prometheus`
      - `monitoring_status`
      - `session_redis`
  * put local modules in the section `# Specific modules not migrated yet, but we don't know if we want`
  * put OCA modules in the section `# OCA modules not available yet, but we don't know if we want`
  * keep the submodule path comment of modules please (i.e. `# OCA/server-tools`)
  * Then commit it as `Add modules from previous project version to uninstall`

It's a bare instance, you are ready to start your migration !

You need to be sure that you can build this bare instance before going further (also called "naked version", as we are keeping at first only standard+enterprise modules here). See [How to build a migration project](./how-to-migration-project-build.md) to run the build.

**WARNING:** This "naked version" is the first DB you can deploy on the cloud platform. You cannot deploy directly the raw DB migrated by Odoo S.A. as a lot of modules are not migrated/available in the `$ADDONS_PATH`, and especially Cloud Platform modules that are needed if you want to avoid unexpected behavior regarding communication with external services (like emails).

Then, and only if the "naked version" is working as expected, you can start to migrate the remaining modules:
* start with external/OCA modules
* then with specific modules as soon as their OCA dependencies (if any) are migrated

To plan the work, better to first start with modules that are used at the beginning of the customer workflow (often CRM/sales ones, no need to start with stock or accounting ones if you're unable to generate the data from the start, that will ease the life of Business Analysts that'll test your work).

Regarding the migration of specific modules located in `odoo/local-src/`, a very useful command to migrate them by keeping their commits history is:

`$ git format-patch --keep-subject --stdout origin/17.0..origin/master -- odoo/local-src/{ADDON} | git am -3 --keep`

This is the same method we use on OCA to migrate modules from one branch to the next one.

### After Go-Live

* Move the master branch to a new one called by the previous version of the project (i.e. `master` to `XX.0`)
* Rename the new version branch to master (i.e. `XX.0` to `master`)
* Et voilà

Finally, we have a branch for the old version and master for the new version.
