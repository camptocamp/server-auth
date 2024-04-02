\set ON_ERROR_STOP on
/*
Makes addons upgrade smooth regarding views.

Context
=======

It is very common that when upgrading addons the existing views in the database
makes the build failing, because each time Odoo tries to load an XML view in
the database, existing views (from the former version, not yet upgraded) are
also taken into account in its inheritance mechanism, and these potential not
up-to-date views makes the upgrade failing.

Details: in version `x` if you have the following addons+inherited views:

    - A/views/a.xml
    - B/views/a_inherited.xml

And in version `x+1` the view `a` has changed so the view `a_inherited` could
not applied anymore, then when you upgrade your addons, Odoo will upgrade
addon `A` first, then `B` (there is no issue at this level), but when it
upgrades `A` it does two things:

    - it loads `a.xml` to update the view in the database (no issue)
    - it also triggers all the inheritance mechanism so it tries to apply the
      existing `a_inherited` view in the database (still in version `x`), but
      here it fails because `a` in `x+1` changed in a incompatible way, and we
      still didn't upgrade `B` to get the `a_inherited` fixed view for `x+1`.

A previous solution was to remove all views from the database and let Odoo
recreates them during the upgrade: this works, but then we lost all the links
to the views regarding actions, filters, reports, mail templates, website...
leading to other errors in cascade.

Solution
========

What we want to achieve here is to preserve view records so we do not lost
any data like:

    - views themself
    - all references to these views (actions, reports, mail templates, etc...)

To do so we disable all views (excepting those already migrated by Odoo SA)
in the database so they won't make addons upgrade failing.
Then, each time Odoo will upgrade an addon, we enable its views right after
so the view inheritance mechanism will be able to find all the required parent
views without been annoyed by views of another addon which is still not upgraded.

To continue the example above this means we disable `a_inherited` (active=False),
and we re-enable it after `B` gets upgraded, because Odoo won't take into account
disabled views when it triggers the inheritance mechanism, avoiding errors.
As Odoo upgrades addons in the right order to respect the dependency tree, all
addons will get their views re-enabled in the right order as well.

NOTE: this script has to be called in pre-core.
*/
-- We start by checking if the 'active_backup' field in 'ir_ui_view' table exists,
-- and invite the developper to create it on the production database if needed.
-- This field will be used to restore the expected states of views (disabled or
-- not) at the end of our migration process because Odoo S.A. migration disables
-- automatically all views that can't be applied anymore on the new code base.
-- This field is automatically created by 'camptocamp_tools' addon too, so in the
-- long run we won't need to create this column manually on the production database.
-- Queries to create the 'active_backup' column:
--
--      ALTER TABLE ir_ui_view ADD COLUMN active_backup BOOLEAN;
--      UPDATE ir_ui_view SET active_backup=active;
--
DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name='ir_ui_view' and column_name='active_backup'
        ) THEN
            ALTER TABLE ir_ui_view ADD COLUMN active_backup BOOLEAN;
            -- Set the right 'active_backup' value for modules already migrated
            UPDATE ir_ui_view SET active_backup=active
            WHERE id IN (
                SELECT res_id FROM ir_model_data
                WHERE module IN (
                    SELECT name FROM ir_module_module
                    WHERE state = 'installed'
                )
            );
            -- Set 'true' by default in 'active_backup' for all other modules
            UPDATE ir_ui_view SET active_backup=true
            WHERE id NOT IN (
                SELECT res_id FROM ir_model_data
                WHERE module IN (
                    SELECT name FROM ir_module_module
                    WHERE state = 'installed'
                )
            );
            RAISE WARNING E'"ir_ui_view.active_backup" column has been automatically created, but consider installing "camptocamp_migration_tools" addon on the production database to get it filled with right values';
        END IF;
    END;
$$;
-- Disable all views excepting standard ones already migrated by Odoo SA.
-- Therefore, views from 'base' addon have to be enable as first inheriting
-- views are based on them.
UPDATE ir_ui_view SET active=false
WHERE id NOT IN (
    SELECT res_id
    FROM ir_model_data
    WHERE model='ir.ui.view'
    AND module IN (
        SELECT name FROM ir_module_module WHERE state='installed'
    )
);
-- Add a trigger to re-enable the views of upgraded addons
CREATE OR REPLACE FUNCTION enable_views_for_upgraded_addons()
  RETURNS TRIGGER
  LANGUAGE PLPGSQL
  AS
$$
BEGIN
    -- Do not trigger this when the update comes from
    -- '{disable/enable}_addons_upgrade.sql' scripts, we want to trigger this
    -- only when Odoo upgrades an addon.
    -- FIXME: maybe not required as we catch only 'installed' states?
    IF (NEW.state NOT ILIKE 'FIXME_%' AND OLD.state NOT ILIKE 'FIXME_%')
    AND NEW.state = 'installed' THEN
        UPDATE ir_ui_view v
        SET active = v.active_backup
        WHERE v.id IN (
            SELECT res_id
            FROM ir_model_data
            WHERE module = NEW.name
            AND model='ir.ui.view'
        )
        AND v.active_backup IS NOT NULL
        -- We re-enable only views which have been updated (having a 'write_date'
        -- set to  today), other ones have probably been removed from the addon
        -- in the new version, so we'll let Odoo removes them cleanly at the end
        -- of its upgrade session.
        AND v.write_date >= DATE(NOW());
    END IF;
    RETURN NEW;
END;
$$;
-- +
DROP TRIGGER IF EXISTS trigger_enable_views_for_upgraded_addons
ON ir_module_module;
CREATE TRIGGER trigger_enable_views_for_upgraded_addons
AFTER UPDATE ON ir_module_module
FOR EACH ROW
EXECUTE PROCEDURE enable_views_for_upgraded_addons();
