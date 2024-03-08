# Using automated tasks with Invoke

This project uses `invoke` to run some automated tasks.

First, install it with:

```bash

$ pip install -r tasks/requirements.txt

```

You can now see the list of tasks by running at the root directory:

```bash

$ invoke --list

```

The tasks are defined in `tasks.py`.

## Some tasks

* [Release bump](#releasebump)
* [Project sync](#projectsync)
* [Translate generate](#translategenerate)
* [Test PR](#testpr)
* [Clean after PR test](#cleanpr)
* [Submodule](#submodule)
    * [Init](#submoduleinit)
    * [Update](#submoduleupdate)
    * [Upgrade](#submoduleupgrade)
    * [List](#submodulelist)
    * [Merges](#submodulemerges)
    * [Show closed prs](#submoduleshow-closed-prs)
    * [List external dependencies installed](#submodulelist-external-dependencies-installed)
* [Database download dump](#databasedownload-dump)
* [Database generate dump](#databasegenerate-dump)
* [Database upload dump](#databaseupload-dump)
* [Database restore from prod](#databaserestore-from-prod)
* [Restore dump on Azure](#databaseazure-restore-dump)
* [Download restore dump](#databasedownload-restore-dump)
* [Create local dump and share on Azure](#databasedump-and-share)
* [Get list of dumps on Azure](#databaselist-of-dumps)
* [Lastpass](#lastpass)
    * [Generate admin pwd](#generate_admin_pwd)
    * [Send admin pwd to lastpass](#send_admin_pwd_to_lpass)
* [Songs rip](#songsrip)
* [Migrate](#migrate)
    * [check-modules](#migratecheck-modules)
    * [reduce-db-size](#migratereduce-db-size)
    * [convert-project](#migrateconvert-project)

#### release.bump

release.bump is used to bump the current version number:
(see [releases.md](docs/releases.md#versioning-pattern) for more informations about versionning)

```
invoke release.bump --feature
# or
invoke release.bump --patch
```

--feature will change the minor version number (eg. 9.1.0 to 9.2.0).
--patch will change the patch version number (eg 9.1.0 to 9.1.1).

bump.release changes following files (which must be commited):
 * [odoo/VERSION](../odoo/VERSION): just contains the project version number, so this version is changed.
 * [HISTORY.rst](../HISTORY.rst): Rename Unreleased section with the new version number and create a new unreleased section.
 * rancher/integration/docker-compose.yml: Change the version of the docker image to use for the integration stack.

-----

#### project.sync

Copy files (such as docs) from the
[odoo-template](https://github.com/camptocamp/odoo-template).
It should be run at a regular basis.

**The file `.sync.yml` is not synced.
You can add itself in the following list to update it once
It will obviously get out of sync again. This is on purpose.**

*NB:* The pre-commit-config is automatically updated
at the end of the sync to exclude uninstallable specific modules.

*PS:* the `DO_SYNC=1` before avoid to re-generate and push the admin password please use it

```
DO_SYNC=1 invoke project.sync
```

-----

#### translate.generate

It generates or updates the pot translation file for an addon.
A new database will be created by the task, in which the addon will be
installed, so we guaranteed to have clean terms.

```
invoke translate.generate odoo/local-src/my_addon
# or
invoke translate.generate odoo/external-src/sale-workflow/my_addon

```

### Test PR

-----
#### pr.test

Script to handle a database and code from pull request, it provides possibility
to test code with database

```
invoke pr.test 539 --get-integration-db=database_name --create-template=True  --base-branch=12.0
```

### Clean after PR test

-----
#### pr.clean

Script to remove git branch and databases after PR test

```
invoke pr.clean 539
```


### Submodule

-----

#### submodule.update

Initialize or update a submodule.

Similar than `git submodule update --init` but more powerful.

Does a `git submodule sync`. Before doing `update`

Download and init each submodules. Will use --reference when
git-autoshare local cache is available.

-s=PATH --submodule-path=PATH Update a single submodule

```
invoke submodule.update
```

or

```
invoke submodule.update -s odoo/external-src/server-tools
```

#### submodule.upgrade

Update and upgrade a submodule.

Update and upgrade each submodules to latest commit in the same branch.

-s PATH --submodule-path=PATH Upgrade a single submodule
-f BRANCH --force-branch=BRANCH Force a specific branch

```
invoke submodule.upgrade
```

or

```
invoke submodule.upgrade -s odoo/external-src/server-tools
```

##### Special parameter

To prevent issue with an upgrade on a submodule which is in a detached HEAD
without any link with a current working remote HEAD (or just master), the command
will ask to fallback in a branch named as Odoo version (90% cases).

This behavior needs improvement, but needs also a better way to specify branches
for submodules in a formalist manner (maybe using `.gitmodules` in a more
precise way).

You can even force a branch for all or a specific submodule.

```
invoke submodule.upgrade -s odoo/external-src/server-tools -f 14.0
```


#### submodule.init

Add git submodules from the `.gitmodules` file configuration.
Instead of using `git submodule add -b 17.0 {url}`
{path}, for every branch you need to add, you can edit the `.gitmodules` file,
add the entries you want, and run this command.


```
invoke submodule.init
```

#### submodule.ls

List submodules paths which can be directly used to directly copy-paste the
addons paths in the Dockerfile. The order depends of the order in the
.gitmodules file.

```
invoke submodule.ls
```

#### submodule.merges

Generate and push a branch including the pending pull requests.

```
invoke submodule.merges odoo/external-src/sale-workflow
```

_Tips : do update all the external submodule you can use_
```shell
for i in $(ls odoo/external-src);
    do invoke submodule.merges odoo/external-src/$i;
done
```


#### submodule.show-closed-prs

Show a list of closed pull requests in the pending merges.

```
invoke submodule.show-closed-prs
```


#### submodule.list-external-dependencies-installed

Compare all modules in an external repository with those in the migration.yml.

```
invoke submodule.list-external-dependencies-installed odoo/external-src/sale-workflow
```

-----

#### database.download-dump

Download Dump from Azure storage.
Platform, customer and environment variables are optional. By, default environment is --env=int (INTEGRATION)
:warning: celebrimbor_cli should already be installed

* with default dump directory `.`

```shell
invoke database.download-dump [dump_name]
```

or

```shell
invoke database.download-dump --platform=[fr|ch] --customer=[enea|init7|...] --env=[int|prod] --dump-name=[dump_name] --dumpdir=[directory_path]
```

`[dump_name]` is Azure dump name, you can get from invoke database.list-of-dumps or invoke database.generate-dump

-----

#### database.generate-dump

Generate Dump on Azure storage.
Platform, customer and environment variables are optional. By, default environment is --env=int (INTEGRATION)
:warning: celebrimbor_cli should already be installed


```shell
invoke database.generate-dump
```

or

```shell
invoke database.generate-dump --platform=[fr|ch] --customer=[enea|init7|...] --env=[int|prod]
```

-----

#### database.upload-dump

Upload Dump on Azure storage.
Platform, customer and environment variables are optional. By, default environment is --env=int (INTEGRATION)
:warning: celebrimbor_cli should already be installed


```shell
invoke database.upload-dump --db-path=[db_path]
```

or

```shell
invoke database.upload-dump --platform=[fr|ch] --customer=[enea|init7|...] --env=[int|prod] --db-path=[db_path]
```

`[db_path]` Path of *.pg dump file

-----

#### database.restore-from-prod

Initiate a replication from the prod environment.
Platform, customer and environment variables are optional. By, default environment is --env=int (INTEGRATION)
:warning: celebrimbor_cli should already be installed


```shell
invoke database.restore-from-prod
```

or

```shell
invoke database.restore-from-prod --platform=[fr|ch] --customer=[enea|init7|...] --env=[int|prod]
```

-----

#### database.azure-restore-dump

Restore uploaded to Azure dump.
Platform, customer and environment variables are optional. By, default environment is --env=int (INTEGRATION)
:warning: celebrimbor_cli should already be installed


```shell
invoke database.azure-restore-dump [dump_name]
```

or

```shell
invoke database.azure-restore-dump --platform=[fr|ch] --customer=[enea|init7|...] --env=[int|prod] --dump-name=[dump_name]
```

`[dump_name]` is Azure dump name, you can get from invoke database.list-of-dumps or invoke database.generate-dump

-----

#### database.download-restore-dump

A combo of download dump from Azure storage and restore it locally.
Platform, customer and environment variables are optional. By, default environment is --env=int (INTEGRATION)
:warning: celebrimbor_cli should already be installed

* with default dump directory `.`

```shell
invoke database.download-restore-dump [dump_name] [dumpdir] [restore_db]
```

or

```shell
invoke database.download-restore-dump --platform=[fr|ch] --customer=[enea|init7|...] --env=[int|prod] --dump-name=[dump_name] --dumpdir=[directory_path] --restore-db=[dump_name]
```

`[dump_name]` is Azure dump name, you can get from invoke database.list-of-dumps or invoke database.generate-dump
`[restore_db]` is name of the database to restore upon

-----

#### database.dump-and-share

A combo of local dump and upload it to Azure storage.
Platform, customer and environment variables are optional. By, default environment is --env=int (INTEGRATION)
:warning: celebrimbor_cli should already be installed

* with default dump directory `/tmp`

```shell
invoke database.dump-and-share [db_name]
```

or

```shell
invoke database.dump-and-share --platform=[fr|ch] --customer=[enea|init7|...] --env=[int|prod] --db-name=[db_name]
```

`[db_name]` is name of the database to dump

-----

#### database.list-of-dumps

Get list of generated dumps for specific platform, customer and environment.
Platform, customer and environment variables are optional. By, default environment is --env=int (INTEGRATION)
:warning: celebrimbor_cli should already be installed


```shell
invoke database.list-of-dumps
```

or

```shell
invoke database.list-of-dumps --platform=[fr|ch] --customer=[enea|init7|...] --env=[int|prod]
```

-----

### LastPass

-----

#### lastpass.gen-admin-pwd

Generate a random admin password.

The password is automatically updated into the admin user setup step in:
odoo/songs/install/pre.py

```
invoke lastpass.gen-admin-pwd
```

-----

#### lastpass.send-admin-pwd-to-lpass

Push admin password to Lastpass.

```
invoke lastpass.send-admin-pwd-to-lpass
```

-----

#### songs.rip

Copy generated songs of a dj.compilation
They come as a zip file which can loaded from a local path or from an odoo url
Files will be placed according to their path in zip file with ./odoo as the root.

When providing an url you can set authentication parameters for the odoo from which
you want to download the compilation.

Usually songs and csv data will be copied in:

odoo/songs/install/generated
and
odoo/data/install/generated

See https://github.com/camptocamp/odoo-dj for more details about dj.compilation


```
invoke songs.rip http://127.0.0.1:8888/dj/download/compilation/account-default-1 [--login admin] [--password admin] [--db odoodb]
# or
invoke songs.rip /tmp/songs.zip
```

-----

### Migrate

-----

#### migrate.check-modules

Used for migration projects,
give information to know which modules are finally installed into databases:

* Migrated database
  * The database returned by Odoo, without applying any script
* Full database
  * The migrated database on which full build has been applied
* Sample database
  * The sample database without customer data

_Example of calling:_
```
invoke migrate.check-modules odoodb-migrated odoodb-full odoodb-sample
```

#### migrate.reduce-db-size

Used for migration projects with large database,
delete lot of data to allow us to test migrated database more easily.

Once time, the build is successfully with light database,
always run a build with full base to be sure deleted data don't break the build.

NB: Due to the choice of delete lot of data without check the foreign keys,
the light db must be used only for build test, not for functional tests.

* Database name
  * The database you want to clean
* Date
  * The date before the data will de deleted

_Example of calling:_
```
invoke migrate.reduce-db-size odoodb 2019-01-01
```

### migrate.convert-project

Used for migration projects, convert the existing project to new version.

An optional argument allow to indicate files/directories to keep in old version.

Actions done by the task:

1. Remove useless files in the old version
2. Remove useless directories in the old version
3. Call the cookiecutter feature to create new project
4. Synchronize files from new project template
5. Rename `__openerp__.py` by `__manifest__.py` in old specific modules
6. Make old specific modules uninstallable

_Example of calling:_
```
invoke migrate.convert-project --paths-to-keep=odoo/local-src,odoo/data/install/company_main_logo.png,scripts
```

NB: For old project without docker, you need to:

* Copy/Paste manually the tasks repository from odoo-template into your project
    * Remove cookicuter tag in `migrate.py` to adapte to your version when you copy the tasks folder
* Call the task with a new argument to move specific addons into odoo/local-src:
```
invoke migrate.convert-project --specific-addon-paths-to-keep=specific-parts/specific-addons --paths-to-keep=odoo/local-src
```

NB: For projects on which we already have the target branch
with some work already done (like specific modules migrated by example),
you can relaunch the invoke task like following example.
Maybe we also can adapt this for normal projects before go live (if needed).

_Example of calling:_
```
invoke migrate.convert-project --paths-to-keep=odoo/local-src,odoo/external-src,odoo/src,pending-merges.d,.pre-commit-config.yaml,.gitmodules,HISTORY.rst
```

Then update manually (at least) following files:
* HISTORY.rst
* odoo/Dockerfile
* odoo/local-src/dummy_test (probably to remove)
* migration.yml
* odoo/requirements.txt
* odoo/data/images/company_main_logo.png
* odoo/songs/install/pre.py (company, languages and password)
* All songs

## Custom tasks

Alongside the core namespaces (release, project. translate), you can create
your own namespace for the need of the project. Dropping a Python file with an
invoke `@task` in the `tasks` directory will make it available in the `invoke`
commands. The namespace will be the name of the file. Let's say you add a
function named `world` decorated with `@task` in a file named `hello.py`, then
the command will be `invoke hello.world`.
