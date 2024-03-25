# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

import anthem
from psycopg2.extensions import AsIs


@anthem.log
def fix_path_on_attachments(ctx, bucket):
    """Fix path on attachments to be compliant with `attachment_azure` module.

    E.g:

    >>> attachment_azure.fix_path_on_attachments(ctx, "evil-daemon-6666")

    Will update `ir_attachment.store_fname` values from:
        `0c03696c5023cc40a1ec2eceec1ecba899dcd107`
    to:
        `azure://evil-daemon-6666/0c03696c5023cc40a1ec2eceec1ecba899dcd107`
    """
    store_type = "azure"
    # Update attachment given by odoo for the database migration
    store_fname_root = ("{}://{}/").format(store_type, bucket)
    query = """
        UPDATE
            ir_attachment
        SET
            store_fname = %s || store_fname
        WHERE
            store_fname IS NOT NULL
        AND store_fname NOT LIKE '%s://%%';
    """
    args = (store_fname_root, AsIs(store_type))
    ctx.env.cr.execute(query, args)
