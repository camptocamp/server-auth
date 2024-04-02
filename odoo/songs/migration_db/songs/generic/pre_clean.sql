-- Display timing of each requests
\timing

-- Since migration to version 13.0,
-- Odoo don't clean all model definitions when uninstalling modules correctly.
-- Then we need to clean them manually.

-- Remaining data in database will be cleaned with database cleanup.


-- Clean models, fields, constrains and relations metadata for uninstalled modules.
-- For models and fields, we only remove the metadata
-- because we can have several metadata on only one object.
DELETE FROM
    ir_model_data
WHERE
    model IN ('ir.model', 'ir.model.fields', 'ir.model.constraint', 'ir.model.relation')
AND
    module IN (
        SELECT
            name
        FROM
            ir_module_module
        WHERE
            state = 'uninstalled'
    );


-- Clean model constrains for uninstalled modules.
DELETE FROM
    ir_model_constraint
WHERE
    module IN (
        SELECT
            id
        FROM
            ir_module_module
        WHERE
            state = 'uninstalled'
    );


-- Clean model relations for uninstalled modules.
DELETE FROM
    ir_model_relation
WHERE
    module IN (
        SELECT
            id
        FROM
            ir_module_module
        WHERE
            state = 'uninstalled'
    );
