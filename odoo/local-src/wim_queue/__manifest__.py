# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
{
    "name": "WIM Queue",
    "summary": "Queue specifications",
    "version": "17.0.1.0.0",
    "category": "Queue",
    "author": "Camptocamp",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "queue_job",
    ],
    "data": [
        # security
        "security/ir.model.access.csv",
        # views
        "views/queue_job_log.xml",
    ],
}
