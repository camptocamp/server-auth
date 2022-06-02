# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
import logging

from odoo import _, api, fields, models
from odoo.addons.queue_job.exception import RetryableJobError
from odoo.addons.queue_job.job import job
from odoo.addons.server_environment import serv_config
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval

from ..lib.sftp_interface import sftp_upload

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):

    _name = "account.move"
    _inherit = ["account.move", "sale.payment.fields.mixin"]

    @api.model
    def _selection_report_to_send(self):
        return [
            ("none", "None"),
            ("invoice_report", "Invoice Report"),
            ("invoice_confirmation", "Invoice Confirmation"),
        ]

    name = fields.Char(index=True)
    state = fields.Selection(index=True)
    customer_number = fields.Char(
        related="partner_id.customer_number", store=True, index=True
    )
    sftp_pdf_path = fields.Char(readonly=True)
    report_to_send = fields.Selection(
        selection="_selection_report_to_send",
        default="invoice_report",
        readonly=True,
    )

    def button_draft(self):
        """Check if any move was pushed onto SFTP to instantiate wizard"""
        # Reimplement odoo checks from super method here. Goal is to avoid
        # these errors popping up after the user did remove the PDF from SFTP
        # COPY OF ODOO CODE
        AccountMoveLine = self.env['account.move.line']
        excluded_move_ids = []

        if self._context.get('suspense_moves_mode'):
            excluded_move_ids = (
                AccountMoveLine.search(
                    AccountMoveLine._get_suspense_moves_domain()
                    + [('move_id', 'in', self.ids)]
                )
                .mapped('move_id')
                .ids
            )

        for move in self:
            if move in move.line_ids.mapped(
                'full_reconcile_id.exchange_move_id'
            ):
                raise UserError(
                    _(
                        'You cannot reset to draft an exchange difference journal entry.'
                    )
                )
            if move.tax_cash_basis_rec_id:
                raise UserError(
                    _(
                        'You cannot reset to draft a tax cash basis journal entry.'
                    )
                )
            if (
                move.restrict_mode_hash_table
                and move.state == 'posted'
                and move.id not in excluded_move_ids
            ):
                raise UserError(
                    _(
                        'You cannot modify a posted entry of this journal because it is in strict mode.'
                    )
                )
        # END COPY OF ODOO CODE
        if not self.env.context.get("_bypass_draft_wizard_check") and any(
            self.mapped("sftp_pdf_path")
        ):
            action = self.env.ref(
                "schweizmobil_sale_subscription.account_move_to_draft_action"
            )
            return action.read()[0]
        return super().button_draft()

    def post(self):
        """Generate queue job to print PDF and push to SFTP for invoices"""
        res = super().post()
        exec_time = safe_eval(
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("sftp.pdf.generation.time")
        )
        execution_date = fields.Datetime.now().replace(
            hour=exec_time.get("hour"),
            minute=exec_time.get("minute"),
            second=exec_time.get("second"),
        )
        for move in self.filtered(
            lambda m: m.type == 'out_invoice' and m.report_to_send != "none"
        ):
            move.with_delay(eta=execution_date)._generate_invoice_pdf()
        return res

    @job(
        default_channel='root.schweizmobil.print_invoice',
        retry_pattern={1: 60, 2: 120, 3: 180, 5: 300},
    )
    def _generate_invoice_pdf(self):
        if self.state != "posted":
            return "Invoice must be posted in order to be printed"
        if self.sftp_pdf_path:
            return "Invoice PDF was already pushed to SFTP"
        # this will raise if the isr setup is not correct
        self.print_ch_qr_bill()
        # but actually we don't need the action, we need the report...
        report_xmlid = self._get_qr_report_xmlid()
        report = self.env.ref(report_xmlid)
        report_content, report_type = report.render(self.ids)
        if report_type != 'pdf':
            if not self.env.context.get('skip_check_invoice_report_type'):
                raise ValueError(
                    "The report type is %s (expecting 'pdf')" % report_type
                )
        if not report_content:
            raise ValueError("The report empty")
        if 'qr' in report_xmlid:
            document_type = 'invoice_2pages'
        else:
            document_type = 'confirmation_1page'
        report_name = safe_eval(report.print_report_name, {'object': self})
        if not report_name.lower().endswith('.pdf'):
            report_name += '.pdf'
        try:
            sftp_path = sftp_upload(report_content, document_type, report_name)
        except Exception as e:
            raise RetryableJobError(str(e)) from e
        # Write SFTP PDF path without environment managed folder (test/prod)
        sftp_root_path = "/" + serv_config.get('sftp', 'root_path') or 'DUMMY'
        self.sftp_pdf_path = sftp_path.lstrip(sftp_root_path)
        return "Invoice PDF has been pushed to SFTP successfully"

    def _get_qr_report_xmlid(self):
        # overridden in schweizmobil_report
        return "l10n_ch.l10n_ch_swissqr_template"
