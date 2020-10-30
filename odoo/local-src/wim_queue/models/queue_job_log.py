# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import fields, models


class QueueJobLog(models.Model):

    _name = "queue.job.log"

    queue_job_id = fields.Many2one("queue.job")
    state = fields.Selection(related="queue_job_id.state")
    uuid = fields.Char(related="queue_job_id.uuid")
    datetime_query = fields.Datetime()
    data = fields.Text()
