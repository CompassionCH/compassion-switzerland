import logging
from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID)

    translations = env['ir.translation'].search([
        ('lang', 'in', ['de_DE', 'fr_CH', 'it_IT']),
        ('src', '=', 'Sponsorships'),
        ('name', '=', 'product.template,plural_name'),
        ('res_id', '=', 2),
        ('module', '=', 'sponsorship_switzerland'),
        ('state', '=', 'to_translate'),
        ('type', '=', 'model')
    ])

    updated_count = 0
    inserted_count = 0

    for translation in translations:
        if translation.lang == 'de_DE':
            translation.value = 'Patenschaften'
        elif translation.lang == 'fr_CH':
            translation.value = 'Parrainages'
        elif translation.lang == 'it_IT':
            translation.value = 'Sponsorizzazioni'

        translation.state = 'translated'
        updated_count += 1

    if updated_count > 0:
        _logger.info(f"Updated {updated_count} translations")

    new_translations = [
        ('de_DE', 'Sponsorships', 'product.template,plural_name', 2, 'sponsorship_switzerland', 'translated', 'Patenschaften', 'model', ''),
        ('fr_CH', 'Sponsorships', 'product.template,plural_name', 2, 'sponsorship_switzerland', 'translated', 'Parrainages', 'model', ''),
        ('it_IT', 'Sponsorships', 'product.template,plural_name', 2, 'sponsorship_switzerland', 'translated', 'Sponsorizzazioni', 'model', '')
    ]

    existing_translations = env['ir.translation'].search([
        ('lang', 'in', ['de_DE', 'fr_CH', 'it_IT']),
        ('src', '=', 'Sponsorships'),
        ('name', '=', 'product.template,plural_name'),
        ('res_id', '=', 2),
        ('module', '=', 'sponsorship_switzerland'),
        ('state', '=', 'translated'),
        ('type', '=', 'model')
    ])

    existing_keys = set(
        (t.lang, t.src, t.name, t.res_id, t.module, t.state, t.type) for t in existing_translations)

    for new_translation in new_translations:
        if tuple(new_translation[:-1]) not in existing_keys:
            env['ir.translation'].create({
                'lang': new_translation[0],
                'src': new_translation[1],
                'name': new_translation[2],
                'res_id': new_translation[3],
                'module': new_translation[4],
                'state': new_translation[5],
                'value': new_translation[6],
                'type': new_translation[7],
                'comments': new_translation[8]
            })
            inserted_count += 1

    if inserted_count > 0:
        _logger.info(f"Inserted {inserted_count} new translations")

