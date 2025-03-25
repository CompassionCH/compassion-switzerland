from odoo import models, api, _
from babel.dates import format_date
from odoo.exceptions import UserError

class ReportEndingSponsorshipCertificate(models.TransientModel):
    _name = 'report.report_compassion.ending_sponsorship_certificate'
    _description = 'Ending Sponsorship Certificate Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['recurring.contract'].browse(docids)

        values = []

        partner_lang = "en_US"

        paragraph_one = {
            "en_US": f"We thank you from the bottom of our hearts for accompanying a child living in poverty.",
            "fr_CH": f"Nous vous remercions du fond du cœur d'avoir accompagné un enfant vivant dans la pauvreté.",
            "de_DE": f"Wir danken dir von ganzem Herzen, dass du ein Kind, das in Armut lebt, begleitet hast.",
            "it_IT": f"Grazie di cuore per aver accompagnato un bambino che vive in estrema povertà.",
        }
        paragraph_two = {
            "en_US": f"Your precious commitment has given dignity to this child, helped him to develop in a promising way and allowed him to look forward to the future with hope.",
            "fr_CH": f"Votre précieux engagement a donné de la dignité à cet enfant, l'a aidé à se développer de manière prometteuse et lui a permis d'envisager l'avenir avec espérance.",
            "de_DE": f"Dein wertvoller Einsatz hat diesem Kind Würde gegeben, ihm zu einer vielversprechenden Entwicklung verholfen und ihm ermöglicht, mit Hoffnung in die Zukunft zu blicken.",
            "it_IT": f"Il tuo prezioso impegno gli ha ridato dignità, lo ha aiutato a svilupparsi in modo promettente e gli ha permesso di guardare al futuro con speranza.",
        }
        paragraph_three = {
            "en_US": f"We thank you from the bottom of our hearts for accompanying a child living in poverty.",
            "fr_CH": f"Nous vous remercions du fond du cœur d'avoir accompagné un enfant vivant dans la pauvreté.",
            "de_DE": f"Wir danken dir von ganzem Herzen, dass du ein Kind, das in Armut lebt, begleitet hast.",
            "it_IT": f"Grazie di cuore per aver accompagnato un bambino che vive in estrema povertà.",
        }



        for doc in docs:

            if not doc.end_date:
                raise UserError(_("End date is required for generating the certificate"))

            if doc.start_date:
                effective_start_date = doc.start_date
            elif doc.activation_date:
                effective_start_date = doc.activation_date
            else:
                raise UserError(_("Either start date or activation date is required for generating the certificate"))

            if doc.partner_id.lang:
                partner_lang = doc.partner_id.lang

            text = (f"<p>{paragraph_one[partner_lang]}</p>"
                    f"<p class = second_paragraph>{paragraph_two[partner_lang]}</p>"
                    )
            long_lasting_text = (f"{paragraph_three[partner_lang]}")

            values.append({
                'doc': doc,
                'long_lasting': doc.contract_duration >= 730,
                'gender': doc.child_id.gender if doc.child_id else 'Unknown',
                'start_date': format_date(effective_start_date, format='MMMM d, yyyy', locale=partner_lang),
                'end_date': format_date(doc.end_date, format='MMMM d, yyyy', locale=partner_lang),
                'pictures': doc.child_id.pictures_ids,
                'child_name': doc.child_id.preferred_name,
                'text': text,
                'long_lasting_text' : long_lasting_text
            })


        return ({
            'docs': values,
            'lang': partner_lang,
        })
