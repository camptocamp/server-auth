/*
This script follows the logic implemented in 'prepare_views_for_upgrade.sql'
executed in pre-core.

Some views hadn't their 'write_date' updated after the addons upgrade (unknown
reason, perhaps because the view definition didn't change between versions?),
so we need to restore their 'active' value as it was in the initial database.

NOTE: this script has to be called after all addons upgrade (i.e. in post-local
or pre-cleanup steps). Better to do it in post-local as developpers don't run
the cleanup step very often and stop at the local one to get a working database.
*/
UPDATE ir_ui_view
SET active = active_backup
WHERE active_backup IS NOT NULL;

-- Set the missing values for 'active_backup' field as core+external addons
-- have been upgraded and added new views but the 'camptocamp_migration_tools'
-- addon hosting this 'active_backup' field wasn't available in the ADDONS_PATH.
-- Having this field correctly set will ease further migrations.
UPDATE ir_ui_view
SET active_backup = active
WHERE active_backup IS NULL;
