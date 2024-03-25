# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

# from odoo.addons.base_dj.utils import csv_from_data
import io
import os

import anthem
import unicodecsv as csv

# The base_dj module is not available for version >= 12.0.
# I copy/paste here the required function


def csv_from_data(fields, rows):
    """Prepare data for CSV."""
    fp = io.BytesIO()
    writer = csv.writer(fp, quoting=csv.QUOTE_ALL, encoding="utf-8")
    writer.writerow(fields)
    for data in rows:
        row = []
        for i, col in enumerate(data):
            if col is False:
                col = None
            row.append(col)
        # writer.writerow([to_str(x, safe=True) for x in row])
        writer.writerow(row)

    fp.seek(0)
    data = fp.read()
    fp.close()
    return data


@anthem.log
def pre_check_fields(ctx):
    """Pre check fields
    Create a CSV file with all fields in the database.
    Used at the end of the build to see
    which fields must be changed of modules.
    To avoid deletion of fields because
    a field has been moved from a module to another.
    """
    ctx.env.cr.execute(
        """
SELECT
    f.model AS model_name,
    d.module AS module_name,
    f.name AS field_name
FROM
    ir_model_fields f
INNER JOIN
    ir_model_data d
        ON f.id = d.res_id
        AND d.model = 'ir.model.fields'
        """
    )
    fields_data = ctx.env.cr.fetchall()

    data = csv_from_data(fields_data[0], fields_data[0:])

    # We can't create this file in another places, for some reasons:
    #  - We can't use the /tmp directory if we want
    #    to keep the file for test or for launch songs manually.
    #  - We can't use environment variable "ODOO_DATA_PATH",
    #    because the directory /data/odoo is a shared volume on which
    #    the owner is the developper.
    #    And the internal user "odoo" used for launch migration
    #    has no rights to write in this repository.
    #    For information, the migration is launched like this:
    #      https://github.com/camptocamp/docker-odoo-project/
    #      blob/master/bin/docker-entrypoint.sh#L120
    with open("/data/odoo/pre_check_fields.csv", "w") as fields_csv:
        fields_csv.write(str(data, "utf-8"))


@anthem.log
def update_base(ctx):
    """Update base

    To see which fields have been deleted in standard build,
    we need to do an update base which will recreate deleted fields.
    """
    ctx.env["ir.module.module"].search(
        [("name", "=", "base")]
    ).button_immediate_upgrade()


@anthem.log
def check_fields(ctx):
    """Check fields

    Compare all fields defined in database between
    the fields before update of modules
    and the fields after update of modules.
    To avoid deletion of fields because
    a field has been moved from a module to another.
    """
    # Get the original fields saved in a CSV file before update of modules
    original_fields = {}
    # The explanation for the chosen directory is in the pre_check_fields.py
    with open("/data/odoo/pre_check_fields.csv") as csvfile:
        reader = csv.reader(csvfile)
        for model_name, module_name, field_name in reader:
            if model_name not in original_fields:
                original_fields[model_name] = {}
            if field_name not in original_fields[model_name]:
                original_fields[model_name][field_name] = []
            original_fields[model_name][field_name].append(module_name)

    # Get the final fields we have now in database
    final_fields = {}
    ctx.env.cr.execute(
        """
SELECT
    f.model AS model_name,
    d.module AS module_name,
    f.name AS field_name
FROM
    ir_model_fields f
INNER JOIN
    ir_model_data d
        ON f.id = d.res_id
        AND d.model = 'ir.model.fields'
        """
    )
    fields_data = ctx.env.cr.fetchall()
    for model_name, module_name, field_name in fields_data:
        if model_name not in final_fields:
            final_fields[model_name] = {}
        if field_name not in final_fields[model_name]:
            final_fields[model_name][field_name] = []
        final_fields[model_name][field_name].append(module_name)

    # For each fields we have now in database,
    # we will compare the list of modules
    # which define this field before and after the update of modules.
    for model_name, model_fields in final_fields.items():
        for field_name, field_modules in model_fields.items():
            if field_name in original_fields.get(model_name, {}):
                original_modules = set(original_fields[model_name][field_name])
                new_modules = set(field_modules)
                if original_modules and original_modules != new_modules:
                    # We have not the same list of modules:
                    # we display a line in build log.
                    ctx.log_line(
                        "PROBLEM ON DEFINED FIELD: "
                        "Model %s / "
                        "Field %s / "
                        "Old modules %s / "
                        "New modules %s"
                        % (
                            model_name,
                            field_name,
                            list(original_modules),
                            list(new_modules),
                        )
                    )


@anthem.log
def pre(ctx):
    """PRE: migration check fields"""
    env = os.environ.get("RUNNING_ENV")
    # We do the check only in dev mode.
    # To avoid to do the check each times,
    # the check is done only if it's not disabled in environment variables.
    if env == "dev":
        migration_check_fields = os.environ.get("MIGRATION_CHECK_FIELDS")
        if migration_check_fields != "True":
            ctx.log_line("If you never check the fields, please do it!")
        else:
            pre_check_fields(ctx)


@anthem.log
def post(ctx):
    """POST: migration check fields"""
    env = os.environ.get("RUNNING_ENV")
    # We do the check only in dev mode.
    # To avoid to do the check each times,
    # the check is done only if it's not disabled in environment variables.
    if env == "dev":
        migration_check_fields = os.environ.get("MIGRATION_CHECK_FIELDS")
        if migration_check_fields != "True":
            ctx.log_line("If you never check the fields, please do it!")
        else:
            update_base(ctx)
            check_fields(ctx)
