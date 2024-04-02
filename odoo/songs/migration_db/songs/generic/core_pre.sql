-- Display timing of each requests
\timing

-- Delete server_config table which broke the build and will be recreated during build
DELETE FROM
    ir_model_data
WHERE
    module = 'server_environment'
AND
    model = 'ir.model.fields'
AND
    res_id IN (SELECT id FROM ir_model_fields WHERE model = 'server.config');
DELETE FROM
    ir_model_data
WHERE
    module = 'server_environment'
AND
    model = 'ir.model'
AND
    res_id IN (SELECT id FROM ir_model WHERE model = 'server.config');
DELETE FROM
    ir_model_fields
WHERE
    model = 'server.config';
DELETE FROM
    ir_model
WHERE
    model = 'server.config';
DROP TABLE
    server_config;


-- Remove all ACL, useful ACL will be recreated during the build
DELETE FROM ir_model_access;
DELETE FROM ir_model_data WHERE model = 'ir.model.access';


-- Remove all ir rules, useful rules will be recreated during the build
DELETE FROM ir_rule;
DELETE FROM ir_model_data WHERE model = 'ir.rule';


-- Odoo upgrade service delivers migrated v15 database with unexpected wrong asset entries
-- to avoid Exception raised here
-- https://github.com/odoo/odoo/blob/6742e410e4c28a1cd24d1f7ea679a563db693f00/odoo/addons/base/models/ir_asset.py#L323
-- we need to remove them, assets will be recreated during the build
DELETE FROM ir_asset;

-- Remove bad column with space at the end.
ALTER TABLE
    res_company
DROP COLUMN IF EXISTS
    "snailmail_cover ";
