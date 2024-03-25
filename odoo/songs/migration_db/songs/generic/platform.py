# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

import os

import anthem


@anthem.log
def post(ctx):
    if os.environ.get("RUNNING_ENV") == "dev":
        return
    # Ensure to migrate relevant attachments to object storage
    ctx.env["ir.attachment"]._force_storage_to_object_storage()
    # Ensure to migrate special attachments from Object Storage back to database
    # This avoids performance issue for fields such as 'image_128' on partners
    # that are fetching the data from the object storage than from the DB
    ctx.env["ir.attachment"].force_storage_to_db_for_special_fields()
