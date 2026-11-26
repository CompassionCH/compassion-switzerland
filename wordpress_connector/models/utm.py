##############################################################################
#
#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#
#    The licence is in the file __manifest__.py
#
##############################################################################


def find_utm(env, model, name):
    """UTM record of the name sent by WordPress, none when it sends no name
    (an empty name matched a source without name: 10'000 donations and
    sponsorships got it)."""
    name = (name or "").strip()
    if not name:
        return env[model]
    return env[model].search([("name", "=", name)], limit=1)
