-- Update the 'state' of addons.
--
-- When we receive the database from the Odoo SA migration service, some addons
-- are 'to install' or 'to upgrade', which makes Odoo installing/upgrading them
-- as soon as we load a Odoo registry in 'pre' step (e.g. with Anthem), causing
-- some issues (addons not available because the list of available addons hasn't
-- been updated at this stage, etc...).
--
-- Disabling the install/upgrade of addons in 'pre' allows us to safely fix data.
--
-- To restore the state of the addons, see the script 'restore_addons_state'

UPDATE
    ir_module_module
SET
    state = 'FIXME_' || state
WHERE
    state IN ('to install', 'to upgrade');
