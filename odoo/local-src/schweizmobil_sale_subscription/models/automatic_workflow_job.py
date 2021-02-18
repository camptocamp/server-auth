# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import api, models


class AutomaticWorkflowJob(models.Model):
    _inherit = "automatic.workflow.job"

    @api.model
    def _validate_invoices(self, validate_invoice_filter):
        move_obj = self.env["account.move"]
        invoices = move_obj.search(validate_invoice_filter)
        res = super()._validate_invoices(validate_invoice_filter)
        for invoice in invoices:
            invoice.with_delay()._generate_invoice_pdf()
        return res
