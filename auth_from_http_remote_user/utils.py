# Author: Laurent Mignon
# Copyright 2014-2018 'ACSONE SA/NV'
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

import random

KEY_LENGTH = 16

randrange = random.SystemRandom().randrange


def randomString(length, chrs):
    """Produce a string of length random bytes, chosen from chrs."""
    n = len(chrs)
    return ''.join([chrs[randrange(n)] for _ in range(length)])


def get_user(users, login):
    """Search for an active user by login name"""
    user = users.sudo().search([
        ('login', '=', login),
        ('active', '=', True)
        ])
    assert len(user) < 2
    if user:
        return user[0]
    return None
