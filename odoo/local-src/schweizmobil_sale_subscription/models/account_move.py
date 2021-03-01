# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
import logging

from odoo import fields, models
from odoo.addons.queue_job.job import job
from odoo.tools.safe_eval import safe_eval

from ..lib.sftp_interface import sftp_upload

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):

    _name = "account.move"
    _inherit = ["account.move", "sale.payment.fields.mixin"]

    customer_number = fields.Char(related="partner_id.customer_number")
    pdf_pushed_to_sftp = fields.Boolean()

    def post(self):
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
        for move in self:
            move.with_delay(
                eta=execution_date.timestamp()
            )._generate_invoice_pdf()
        return res

    @job(default_channel='root.schweizmobil.print_invoice')
    def _generate_invoice_pdf(self):
        if self.state != "posted":
            return "Invoice must be posted in order to be printed"
        if self.pdf_pushed_to_sftp:
            return "Invoice PDF was already pushed to SFTP"
        # this will raise if the isr setup is not correct
        self.isr_print()
        # but actually we don't need the action, we need the report...
        report_xmlid = self._get_isr_report_xmlid()
        report = self.env.ref(report_xmlid)
        report_content, report_type = report.render(self.ids)
        if report_type != 'pdf':
            if not self.env.context.get('skip_check_invoice_report_type'):
                raise ValueError(
                    "The report type is %s (expecting 'pdf')" % report_type
                )
        if not report_content:
            raise ValueError("The report empty")
        if 'isr' in report_xmlid:
            document_type = 'invoice'
        else:
            document_type = 'confirmation'
        report_name = safe_eval(report.print_report_name, {'object': self})
        if not report_name.lower().endswith('.pdf'):
            report_name += '.pdf'
        sftp_upload(report_content, document_type, report_name)
        self.pdf_pushed_to_sftp = True
        return True

    def _get_isr_report_xmlid(self):
        # overridden in schweizmobil_report
        return "l10n_ch.l10n_ch_isr_report"
