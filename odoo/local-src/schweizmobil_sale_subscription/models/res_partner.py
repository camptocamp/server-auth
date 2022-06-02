# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
import logging
from datetime import date

from odoo import fields, models
from odoo.addons.queue_job.job import job
from odoo.tools.translate import _

from ..lib.sftp_interface import sftp_upload

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = "res.partner"

    # TODO: Drop me
    # This field is used to define if a partner had multiple subscriptions
    # before the import from dynamics
    pre_import_multi_subs = fields.Boolean()

    def _cron_execute_followup_print_letters(self):
        followup_data = self._query_followup_level(all_partners=True)
        in_need_of_action = self.env['res.partner'].browse(
            [
                d['partner_id']
                for d in followup_data.values()
                if d['followup_status'] == 'in_need_of_action'
            ]
        )
        in_need_of_action_print_letter = in_need_of_action.filtered(
            lambda p: p.followup_level.print_letter
        )
        _logger.info(
            'Generating jobs for %d partner follow ups', len(in_need_of_action)
        )
        count = 0
        for partner in in_need_of_action_print_letter:
            partner_tmp = partner._execute_followup_partner()
            if partner_tmp != partner:
                # this should never happen given the filtering we are doing
                _logger.error(
                    'res_partner._execute_followup_partner '
                    'returned a different partner for %s -> %s',
                    partner,
                    partner_tmp,
                )
                continue
            if partner_tmp:
                partner_tmp.with_delay()._generate_followup_pdf()
                count += 1
        _logger.info('Done generating %d jobs', count)

    @job(default_channel='root.schweizmobil.print_invoice')
    def _generate_followup_pdf(self):
        self.ensure_one()
        report = self.env.ref('account_followup.action_report_followup')
        report_content, report_type = report.render(self.ids)
        if report_type != 'pdf':
            raise ValueError("The report type is %s (expecting 'pdf')")
        if not report_content:
            raise ValueError("The report empty")
        self.message_post(body=_('Follow-up letter printed'))
        filename = 'Followup-QR_{}_{}.pdf'.format(
            date.today().strftime('%Y-%m-%d'),
            self.customer_number or 'no_customer_number',
        )
        sftp_upload(report_content, 'followup', filename)
        return True
