from uuid import uuid4

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    company = env["res.company"].search([])
    company.write(
        {
            "social_linkedin": (
                "https://www.linkedin.com/company/compassion-schweiz-suisse-svizzera"
            ),
            "social_instagram": "https://www.instagram.com/compassionswiss/",
            "social_vimeo": "https://vimeo.com/compassionswitzerland",
        }
    )
    langs = env["res.lang"].get_installed()
    migrate_date = {
        "en_US": {
            "commercial_name": "Compassion Switzerland",
            "commercial_street": "Parkterrasse 10",
            "commercial_city": "Bern",
            "commercial_zip": "3012",
            "commercial_phone": "+41 (0)31 552 21 25",
            "social_facebook": "https://www.facebook.com/compassionschweiz",
            "social_youtube": "https://www.youtube.com/@compassionschweiz3020",
        },
        "fr_CH": {
            "commercial_name": "Compassion Suisse",
            "commercial_street": "Rue Galilée 3",
            "commercial_city": "Yverdon-les-Bains",
            "commercial_zip": "1400",
            "commercial_phone": "+41 (0)24 434 21 24",
            "social_facebook": "https://www.facebook.com/compassionsuisse/",
            "social_youtube": "https://www.youtube.com/@compassionsuisse",
        },
        "de_DE": {
            "commercial_name": "Compassion Schweiz",
            "commercial_street": "Parkterrasse 10",
            "commercial_city": "Bern",
            "commercial_zip": "3012",
            "commercial_phone": "+41 (0)31 552 21 21",
            "social_facebook": "https://www.facebook.com/compassionschweiz",
            "social_youtube": "https://www.youtube.com/@compassionschweiz3020",
        },
        "it_IT": {
            "commercial_name": "Compassion Svizzera",
            "commercial_street": "Parkterrasse 10",
            "commercial_city": "Bern",
            "commercial_zip": "3012",
            "commercial_phone": "+41 (0)31 552 21 24",
            "social_facebook": "https://www.facebook.com/compassionsvizzera",
            "social_youtube": "https://www.youtube.com/@compassionsvizzera",
        },
    }
    for lang_code, _ in langs:
        company.with_context(lang=lang_code).write(migrate_date[lang_code])
    employees = (
        env["hr.employee"]
        .with_context(active_test=False)
        .search(["|", ("uuid", "=", False), ("uuid", "=", "")])
    )
    for employee in employees:
        employee.uuid = str(uuid4())
