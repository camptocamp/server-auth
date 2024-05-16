# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import _, exceptions, fields, models


class WIMSaleSubscription(models.Model):
    _name = 'wim.sale.subscription'
    _inherit = 'wim.binding'
    _inherits = {'sale.order': 'odoo_id'}
    _description = 'WIM Subscription'

    odoo_id = fields.Many2one(
        comodel_name='sale.order',
        string='Subscription',
        required=True,
        index=True,
        ondelete='restrict',
    )
    external_id = fields.Char(related="odoo_id.partner_id.customer_number")


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    wim_bind_ids = fields.One2many(
        comodel_name='wim.sale.subscription',
        inverse_name='odoo_id',
        copy=False,
        string='Subscription Bindings',
        context={'active_test': False},
        readonly=True,
    )

    def _get_renewal_payment_term(self):
        res = super()._get_renewal_payment_term()
        if not res:
            res = self.wim_bind_ids.backend_id.first_invoice_payment_term_id
        return res

    def _prepare_invoice_data(self):
        """
        Apply distinct payment term for subscriptions and sale orders.
        """
        res = super()._prepare_invoice_data()
        if self.wim_bind_ids:
            backend = self.wim_bind_ids.backend_id
            payment_term = backend.recurring_invoice_payment_term_id
            res.update(invoice_payment_term_id=payment_term.id)
        return res

    def setup_binding(self):
        backend = self.env["wim.backend"].get_singleton()
        for sub in self:
            if sub.wim_bind_ids:
                raise exceptions.UserError(
                    _("Connector binding already set on subscription %s") % sub.name
                )
            if not sub.partner_id.wim_bind_ids:
                raise exceptions.UserError(
                    _(
                        "Connector binding cannot be set on subscription %s "
                        "whose partner has no connector binding."
                    )
                    % sub.name
                )
            sub.write({"wim_bind_ids": [(0, 0, {"backend_id": backend.id})]})

    def _write(self, vals):
        """Force triggering of connector export after field computation"""
        res = super()._write(vals)
        if "next_online_renewal_date" in vals:
            for record in self:
                self._event("on_record_write").notify(
                    record, fields=["next_online_renewal_date"]
                )
        return res
