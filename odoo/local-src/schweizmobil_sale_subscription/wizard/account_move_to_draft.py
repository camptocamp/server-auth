# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class AccountMoveToDraft(models.TransientModel):
    _name = "account.move.to.draft"
    _description = "Confirmation wizard for invoices pushed onto SFTP"

    move_ids = fields.Many2many("account.move")
    message = fields.Html(readonly=True)
    removed_from_sftp = fields.Boolean()

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        active_ids = self.env.context.get("active_ids", [])
        if "move_ids" in fields_list:
            res["move_ids"] = active_ids
            if "message" in fields_list:
                moves = self.env["account.move"].browse(active_ids)
                sftp_moves = moves.filtered(lambda m: m.sftp_pdf_path)
                message_lines = "</li><li>".join([m.sftp_pdf_path for m in sftp_moves])
                res["message"] = "<ul><li>" + message_lines + "</li></ul>"
        return res

    def action_confirm(self):
        if not self.removed_from_sftp:
            raise UserError(
                _(
                    "Cannot reset invoices back to draft without user's "
                    "confirmation when the PDFs were already pushed on SFTP."
                )
            )
        res = self.move_ids.with_context(_bypass_draft_wizard_check=True).button_draft()
        self.move_ids.write({"sftp_pdf_path": "", "attachment_ids": [(5, 0, 0)]})
        return res
