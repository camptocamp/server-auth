# Copyright 2021 Camptocamp SA
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl)
from dateutil.relativedelta import relativedelta

from odoo import fields, models


class SaleSubscription(models.Model):

    _inherit = "sale.subscription"

    def increment_period(self):
        res = super().increment_period()
        if not self.env.context.get("_reset_sub_dates"):
            return res
        today = fields.Date.today()
        for subscription in self:
            duration_type = subscription.recurring_rule_type
            duration = subscription.template_id.recurring_rule_count
            periods = {
                "daily": "days",
                "weekly": "weeks",
                "monthly": "months",
                "yearly": "years",
            }
            recurring_next_date = subscription._get_recurring_next_date(
                subscription.recurring_rule_type,
                subscription.recurring_interval,
                today,
                subscription.recurring_invoice_day,
            )
            vals = {
                "date_start": today,
                "recurring_next_date": recurring_next_date,
            }
            if subscription.recurring_rule_boundary == 'limited':
                end_date = today + relativedelta(
                    **{periods[duration_type]: duration}
                )
                vals["date"] = end_date
            subscription.write(vals)
        return res
