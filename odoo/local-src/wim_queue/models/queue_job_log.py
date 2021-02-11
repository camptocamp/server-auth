# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import fields, models

RESULT_STATE = [("success", "Successful"), ("failed", "Failed")]


class QueueJobLog(models.Model):

    _name = "queue.job.log"
    _description = "Log queue job requests"

    queue_job_id = fields.Many2one("queue.job")
    job_state = fields.Selection(
        string="Job State", related="queue_job_id.state"
    )
    state = fields.Selection(
        RESULT_STATE,
        string="Action State",
        help="Whether the action was successfully executed or not",
    )
    result = fields.Text(help="Result of the executed action")
    uuid = fields.Char(related="queue_job_id.uuid")
    datetime_query = fields.Datetime()
    data = fields.Text()
