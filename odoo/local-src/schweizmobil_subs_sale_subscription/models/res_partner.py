# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
import logging
from datetime import date

from odoo import api, models, tools
from odoo.tools.translate import _

from ..lib.sftp_interface import sftp_upload

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = "res.partner"

    def _cron_execute_followup_print_letters(self):
        followup_data = self._query_followup_data(all_partners=True)
        in_need_of_action = self.env['res.partner'].browse(
            [
                d['partner_id']
                for d in followup_data.values()
                if d['followup_status'] == 'in_need_of_action'
            ]
        )

        in_need_of_action_print_letter = in_need_of_action.filtered(
            lambda p: any(inv.report_to_send != "none" for inv in p.unpaid_invoice_ids)
        )

        _logger.info(
            'Generating jobs for %d partner follow ups', len(in_need_of_action)
        )
        count = 0
        for partner in in_need_of_action_print_letter:
            partner_tmp = partner._execute_followup_partner()
            if partner_tmp:
                # For test run, Job accepts only methods of Models
                if not tools.config['test_enable']:
                    partner.with_delay()._generate_followup_pdf()
                else:
                    partner._generate_followup_pdf()
                count += 1
            else:
                # this should never happen given the filtering we are doing
                _logger.error(
                    'res_partner._execute_followup_partner '
                    'returned a different partner for %s',
                    partner,
                )
                continue
        _logger.info('Done generating %d jobs', count)

    @api.model
    def _generate_followup_pdf(self):
        self.ensure_one()
        report_content, report_type = self.env['ir.actions.report']._render_qweb_pdf(
            'account_followup.action_report_followup', self.ids
        )
        if report_type != 'pdf' and not tools.config['test_enable']:
            raise ValueError("The report type is %s (expecting 'pdf')")
        if not report_content:
            raise ValueError("The report empty")
        if not tools.config['test_enable']:
            self.message_post(body=_('Follow-up letter printed'))
            filename = 'Followup-QR_{}_{}.pdf'.format(
                date.today().strftime('%Y-%m-%d'),
                self.customer_number or 'no_customer_number',
            )
            sftp_upload(report_content, 'followup_2pages', filename)
        return True
