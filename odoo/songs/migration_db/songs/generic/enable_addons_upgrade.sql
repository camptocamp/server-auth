-- See explanations on `disable_addons_upgrade.sql`.

UPDATE
    ir_module_module
SET
    state = REPLACE(state, 'FIXME_', '')
WHERE
    state like 'FIXME_%';
