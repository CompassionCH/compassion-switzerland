# ruff: noqa: E501 -- email template HTML, kept on one line per paragraph
import json
from typing import Any

from openupgradelib import openupgrade

STEP1_EMAIL_XMLID = "website_switzerland.group_visit_step1_email"
STEP1_CONFIG_XMLID = "website_switzerland.group_visit_step1_config"
STEP2_EMAIL_XMLID = "website_switzerland.group_visit_step2_email"
STEP2_CONFIG_XMLID = "website_switzerland.group_visit_step2_config"

STEP1_VARS = """<t t-set="partner" t-value="object.partner_id"/>
    <t t-set="registration" t-value="object.get_objects()"/>
    <t t-set="event" t-value="registration.compassion_event_id"/>
    <t t-set="down_payment" t-value="registration.down_payment_id"/>
"""


def _step1_button(url, text_button):
    return f"""
    <div style="margin:40px auto; text-align: center;">
            <a t-att-href="{url}" style="text-decoration:none;padding:12px 18px;font-size: 12px; line-height: 18px; color: white; display: inline-block; margin-bottom: 0px; font-weight: 400; text-align: center; vertical-align: middle; cursor: pointer; white-space: nowrap; background-image: none; background-color: #2A5EEC; border: 1px solid #2A5EEC; border-radius:3px">
                {text_button}
            </a>
        </div>
"""


def _swap_group_visit_xmlids(env: Any):
    """Restore the swapped group visit email XML IDs if the DB still has them crossed."""
    step1 = env.ref(STEP1_EMAIL_XMLID, raise_if_not_found=False)
    step2 = env.ref(STEP2_EMAIL_XMLID, raise_if_not_found=False)
    if not step1 or not step2:
        return

    openupgrade.logged_query(
        env.cr,
        "UPDATE ir_model_data SET name = %s WHERE module = %s AND name = %s",
        (
            "__tmp_group_visit_step1_email",
            "website_switzerland",
            "group_visit_step1_email",
        ),
    )
    openupgrade.logged_query(
        env.cr,
        "UPDATE ir_model_data SET name = %s WHERE module = %s AND name = %s",
        (
            "__tmp_group_visit_step1_config",
            "website_switzerland",
            "group_visit_step1_config",
        ),
    )
    openupgrade.logged_query(
        env.cr,
        "UPDATE ir_model_data SET name = %s WHERE module = %s AND name = %s",
        ("group_visit_step1_email", "website_switzerland", "group_visit_step2_email"),
    )
    openupgrade.logged_query(
        env.cr,
        "UPDATE ir_model_data SET name = %s WHERE module = %s AND name = %s",
        ("group_visit_step1_config", "website_switzerland", "group_visit_step2_config"),
    )
    openupgrade.logged_query(
        env.cr,
        "UPDATE ir_model_data SET name = %s WHERE module = %s AND name = %s",
        (
            "group_visit_step2_email",
            "website_switzerland",
            "__tmp_group_visit_step1_email",
        ),
    )
    openupgrade.logged_query(
        env.cr,
        "UPDATE ir_model_data SET name = %s WHERE module = %s AND name = %s",
        (
            "group_visit_step2_config",
            "website_switzerland",
            "__tmp_group_visit_step1_config",
        ),
    )


STEP1_BODY = {
    "en_US": STEP1_VARS
    + """<p t-out="partner.salutation"></p>
<p>
    Your registration for the <t t-out="event.name"></t> is progressing well. Thank you very much for your interest in Compassion's
    work to free more children from poverty every day, for a dignified and meaningful life.
</p>
<p>
    To confirm your registration, you only need to pay a deposit of <t t-out="down_payment.currency_id.symbol"/>
    <t t-out="'{:,.0f}'.format(down_payment.amount_total_signed)"/>.- You have the choice to make this payment:
</p>
<ul>
    <li>
        Online by Credit card or Postfinance card
        """
    + _step1_button("registration.down_payment_link", "Online payment")
    + """
    </li>
    <li>
        By paying using the payment slip attached to this email
    </li>
</ul>
<p>
    We thank you in advance for making this payment today or in the coming days.
</p>
<p>
    The next step will be to prepare for the trip. Here again, you will receive the information you need to know in time
    to make this trip an enriching and unforgettable experience for you.
</p>
<p>
    Once again, thank you for your commitment to children in need.
</p>
<p>
    Warm regards
</p>
<t t-out="object.user_id.signature" />""",
    "fr_CH": STEP1_VARS
    + """<t t-set="children_in_poverty" t-value="object.get_snippet('children_in_poverty', strip_html=True)"/>
<p t-out="partner.salutation">
</p>
<p>
    Merci de vous être inscrit<t t-out="partner.get('accord_e')"></t> au voyage Impact de Compassion <t t-out="event.country_id.in_preposition"></t> <t t-out="event.country_id.name"></t>.
</p>
<p>
    Ensemble, nous pouvons allier voyage et impact concret pour les mamans et leurs bébés sur place.
</p>
<p>
    Pour que nous puissions confirmer votre inscription, voici les deux étapes nécessaires.
</p>
<p>
    Première étape: <b>merci de nous verser l'acompte de <t t-out="down_payment.currency_id.symbol"></t> <t t-out="'{:,.0f}'.format(down_payment.amount_total_signed)"/>.- aujourd'hui ou dans les prochains jours</b>. Vous pouvez effectuer le paiement:
</p>
<ul>
    <li>
        en utilisant le bulletin de versement en pièce jointe
    </li>
    <li>
        ou en ligne par carte de crédit.
    </li>
</ul>"""
    + _step1_button("registration.down_payment_link", "Payer en ligne")
    + """
<p>
    Deuxième étape: dans un prochain e-mail, nous vous informerons de la politique de protection des enfants et des documents requis.
</p>
<p>
    Nous sommes impatients de vous faire découvrir comment un parrainage peut transformer la vie d'un enfant et celle de ses proches. Mais aussi d'aiguiser votre regard sur l'extrême pauvreté dans laquelle vivent encore <t t-out="children_in_poverty "></t> millions d'enfants aujourd'hui.

</p>
<p>
    Si vous avez des questions, n'hésitez pas à nous contacter par e-mail à <t t-out="object.user_id.email"></t>.
</p>
<p>
    Recevez nos chaleureuses salutations. A bientôt!
</p>
<t t-out="object.user_id.signature"></t>""",
    "de_DE": STEP1_VARS
    + """
      <t t-set="children_in_poverty" t-value="object.get_snippet('children_in_poverty', strip_html=True)"/>
    <t t-set="du" t-value="partner.get('du')"/>
    <t t-set="dein" t-value="partner.get('dein')"/>
    <t t-set="deine" t-value="partner.get('deine')"/>
    <t t-set="dir" t-value="partner.get('dir')"/>
    <t t-set="dich" t-value="partner.get('dich')"/>

<p t-out="partner.salutation"/>
<p>
    Herzlichen Dank für <t t-out="deine"/> Anmeldung für die Impact-Reise in die <t t-out="event.country_id.name"/> mit Compassion.
</p>
<p>
    Es ist grossartig, gemeinsam mit <t t-out="dir"/> einen konkreten Impact für Mütter und ihre Babys vor Ort bewirken zu können.
</p>
<p>
    Damit wir <t t-out="deine"/> Anmeldung definitiv bestätigen können, sind nur noch zwei Schritte erforderlich.
</p>
<p>
    Erster Schritt: Danke, dass <t t-out="du"/> uns die Anzahlung von <t t-out="down_payment.currency_id.symbol"/> <t t-out="'{:,.0f}'.format(down_payment.amount_total_signed)"/>.- heute oder in den nächsten Tagen überweist. <t t-out="du.title()"/> <t t-out="'könnt' if partner.plural else 'kannst'"/> die Zahlung:
</p>
<ul>
    <li>
        entweder mit dem Einzahlungsschein im Anhang ausführen
    </li>
    <li>
        oder online per Kreditkarte tätigen
    </li>
</ul>
  """
    + _step1_button("registration.down_payment_link", "Onlinezahlung")
    + """
  <p>
    Zweiter Schritt: In einer nächsten E-Mail werden wir <t t-out="dich"/> über die Richtlinien zum Kinderschutz und die benötigten Dokumente informieren.
</p>
<p>
    Wir freuen uns darauf, <t t-out="dir"/> zu zeigen, wie eine Patenschaft das Leben eines Kindes und das seiner Angehörigen verändern kann. Aber auch, <t t-out="deine"/>n Blick für die extreme Armut zu schärfen, in der heute noch <t t-out="children_in_poverty "/> Millionen Kinder leben.
</p>
<p>
    Wenn <t t-out="du"/> Fragen <t t-out="'habt, dürft ihr' if partner.plural else 'hast, darfst du'"/> uns gerne per E-Mail an <t t-out="object.user_id.email"/> kontaktieren.
</p>
<p>
  Liebe Grüsse
</p>
  <t t-out="object.user_id.signature"/>""",
}

FEEDBACK_VARS = """<t t-set="partner" t-value="object.partner_id"/>
    <t t-set="registration" t-value="object.get_objects()"/>
    <t t-set="event" t-value="registration.compassion_event_id"/>
    <t t-set="survey" t-value="registration.feedback_survey_id or registration.event_id.feedback_survey_id"/>
    <t t-set="user" t-value="registration.event_id.user_id"/>
    <t t-set="base_url" t-value="registration.website_id.domain"/>
    <t t-set="url" t-value="base_url + survey.sudo().get_start_url()"/>
    <t t-set="children_in_poverty" t-value="object.get_snippet('children_in_poverty', strip_html=True)"/>
    """
FEEDBACK_BODY = {
    "en_US": FEEDBACK_VARS
    + """<p t-out="partner.salutation"/>
<p>We hope that you have returned from your journey with Compassion and that this experience has enriched you in every way.
    <br/>
    <br/>
    Would you be able to take 3 minutes to share your thoughts on this trip with us?
    <br/>
    <br/>
</p>"""
    + _step1_button("url", "Share us your feedback")
    + """
<p>
    Did you know that? Your trip can have an even greater impact. To do this, simply tell your friends and share your sponsorship experience.
    <br/>
    <br/>
    In this way, some of your loved ones could imitate you and in turn transform a child's life, by committing to sponsor a child.
    <br/>
    <br/>
    Encourage them to sponsor a child by sending the message "1 child" by SMS to 959 (free) or directly on www.compassion.ch.
    <br/>
    <br/>
    Feel free to contact us if you would like to be advised on how to organize a small meeting with your friends at home and/or to receive material for this purpose. We are available by phone on 031 552 21 25 or by email at events@compassion.ch.
    <br/>
    <br/>
    At Compassion, we believe that it is possible to change the world, one child at a time. Even if extreme poverty declines - and this is good news - there are still 385 million children living in extreme poverty.
    <br/>
    <br/>
    Thank you very much for your commitment to working with us to transform the lives of as many of these children as possible.
    <br/>
    <br/>
    Receive our warmest greetings.
</p>
<t t-out="user.signature" />""",
    "de_DE": FEEDBACK_VARS
    + """<p>
    <t t-out="partner.informal_salutation"/>
    <br/>
    <br/>
    Wir hoffen, dass du nach der Reise mit Compassion wieder gut nach Hause gekommen bist und dass das Erlebte für dich in jederlei Hinsicht eine Bereicherung war.
    <br/>
    <br/>
    Hast du drei Minuten, uns deine Meinung zur Reise mitzuteilen?
    <br/>
    <br/>
</p>"""
    + _step1_button("url", "Feedback senden")
    + """
<p>
Deine Reise kann noch weitreichende Auswirkungen haben. Wusstest du das? Wenn du deinen Freunden und Bekannten von deinen Erlebnissen und der Begegnung mit deinem Patenkind berichtest, werden manche daraufhin deinem Beispiel folgen, eine Patenschaft übernehmen und so ihrerseits das Leben eines Kindes verändern.
<br/>
<br/>
Ermutige deine Freunde, Pate eines Kindes zu werden! Dazu können sie eine gratis SMS mit dem Text "1 Kind" an 959 senden oder aber sie gehen direkt auf www.compassion.ch /jetzt : Dort findet ihr Kinder, für die wir gerade dringend einen Paten suchen.
<br/>
<br/>
Möchtest du Compassion bei einem kleinen Freundestreffen bei dir zu Hause vorstellen und brauchst du dazu unsere Unterstützung bzw. Material, dann melden dich ungeniert! Ruf' uns an 024 434 21 24 oder schreibe uns an events@compassion.ch .
<br/>
<br/>
Wir von Compassion glauben daran, dass es möglich ist, die Welt zu verändern - ein Kind nach dem anderen. Auch wenn extreme Armut abnimmt- was eine gute Nachricht ist - leben noch immer <t t-out="children_in_poverty"/> Millionen Kinder in extremer Armut.
<br/>
<br/>
Von Herzen danke, dass du dich Seite an Seite mit uns engagierst, um das Leben möglichst vieler Kinder zu verändern!
<br/>
<br/>
Herzliche Grüsse
</p>
<t t-out="user.signature" />
""",
    "fr_CH": FEEDBACK_VARS
    + """
<p t-out="partner.salutation"></p>
    <p>
    Nous espérons que vous êtes bien rentré<t t-out="partner.get('accord_e') or ''"/> de votre voyage avec Compassion et que cette expérience vous a enrichi<t t-out="partner.get('accord_e') or ''"/> en tous points de vue.
    <br/>
    <br/>
    Vous serait-il possible de prendre 3 minutes pour nous partager votre avis sur ce voyage ?
    <br/>
    <br/>
</p>"""
    + _step1_button("url", "Envoyez votre feedback")
    + """
<p>
Le saviez-vous ? Votre voyage peut avoir un impact encore plus grand. Pour cela, il vous suffit d'en parler à vos amis et de témoigner de votre expérience de parrainage.
<br/>
<br/>
Ainsi, certains de vos proches pourraient vous imiter et transformer à leur tour la vie d'un enfant, en s'engageant à parrainer un enfant.
<br/>
<br/>
Encouragez-les ensuite à parrainer un enfant en envoyant le message "1 enfant" par SMS au 959 (gratuit) ou directement sur www.compassion.ch.
<br/>
<br/>
N'hésitez pas à prendre contact avec nous si vous souhaitez être conseillé(e) pour l'organisation d'une petite rencontre avec vos amis chez vous et/ou pour recevoir du matériel dans ce but. Nous sommes disponibles par téléphone au 024 434 21 24 ou par courriel events@compassion.ch.
<br/>
<br/>
A Compassion, nous croyons qu'il est possible de changer le monde, un enfant à la fois. Même si l'extrême pauvreté recule -et c'est une bonne nouvelle- il reste néanmoins <t t-out="children_in_poverty"/> millions d'enfants qui vivent dans l'extrême pauvreté.
<br/>
<br/>
Merci de tout cœur de votre engagement à nos côtés pour transformer la vie d'un maximum de ces enfants.
<br/>
<br/>
Recevez nos chaleureuses salutations.
</p>
<t t-out="user.signature" />""",
}
FEEDBACK_SUBJECT = {
    "en_US": "How did your trip with Compassion go?",
    "de_DE": "Wie war deine Reise {{object.get_objects().compassion_event_id.country_id.in_preposition}} {{object.get_objects().compassion_event_id.country_id.name}}?",
    "fr_CH": "Comment s'est passé votre voyage {{object.get_objects().compassion_event_id.country_id.in_preposition}} {{object.get_objects().compassion_event_id.country_id.name}} ?",
}

MEDICAL_VARS = """<t t-set="partner" t-value="object.partner_id"/>
<t t-set="registration" t-value="object.get_objects()"/>
<t t-set="event" t-value="registration.compassion_event_id"/>
<t t-set="base_url" t-value="registration.website_id.domain"/>
<t t-set="user" t-value="registration.event_id.user_id"/>
<t t-set="survey" t-value="registration.medical_survey_id or registration.event_id.medical_survey_id"/>
"""
MEDICAL_BODY = {
    "fr_CH": MEDICAL_VARS
    + """<p t-out="partner.salutation"></p>
   <p>
   Encore une fois, merci de votre intérêt pour le travail de Compassion au profit des enfants vivant dans l'extrême pauvreté. Nous nous réjouissons de votre voyage <t t-out="event.country_id.in_preposition"/> <t t-out="event.country_id.name"/>.
   <br/>
   <br/>
   Il est temps de préparer le voyage sur le plan de la santé. Le séjour qui vous attend sera intéressant. Il peut être éprouvant aussi : longs vols internationaux, décalage horaire, changements d'altitude, déplacements sur des routes sommaires, randonnées sur des terrains accidentés et longues journées seront possibles.
   <br/>
   <br/>
   Parce que nous savons que chaque individu est différent, nous recueillons des renseignements sur la santé de chaque personne inscrite afin d'être au courant de ses limites et de ses besoins spécifiques.
   <br/>
   <br/>
   Cliquez ici pour contrôler la check-list et bien préparer ce voyage sur le plan de la santé ;
   <br/>
   <br/>
  </p>
  """
    + _step1_button("base_url + survey.get_start_url()", "Vers la check-list médicale")
    + """
  <p>
  Merci de votre engagement pour les enfants démunis.
  <br/>
  <br/>
  Recevez nos chaleureuses salutations.
  </p>
   <t t-out="user.signature"/>""",
    "de_DE": MEDICAL_VARS
    + """<p t-out="partner.salutation"/>
   <p>
   Danke von ganzem Herzen, dass du dich für Kinder, die in extremer Armut leben, Seite an Seite mit uns engagierst. Wir freuen uns, dass du mit uns reist!
   <br/>
   <br/>
   Jetzt ist es an der Zeit, die nötigen Gesundheitsvorkehrungen für die Reise zu treffen. Dein bevorstehender Aufenthalt im Ausland wird spannend! Er wird aber vielleicht auch etwas anstrengend sein: lange Flugzeiten, Zeitverschiebung, Höhenunterschiede, Reisen auf unbefestigten Strassen, Fussmärsche auf unebenen Wegen und lange Tage; all das kann auf dich zukommen.
   <br/>
   <br/>
   Da jeder Mensch unterschiedlich ist, holen wir von jeder angemeldeten Person Auskunft über ihren Gesundheitszustand ein, damit wir über die Grenzen und spezifischen Bedürfnisse eines jeden informiert sind.
   <br/>
   <br/>
   Klicke hier, um die Check-Liste durchzugehen und dich aus gesundheitlicher Sicht gut auf die Reise vorzubereiten:
  </p>
  """
    + _step1_button("base_url + survey.get_start_url()", "Zur Check-Liste")
    + """
  <p>
  Danke für dein Engagement für Kinder in Armut!
  <br/>
  <br/>
  Herzliche Grüsse
   </p>
   <t t-out="user.signature"/>
   """,
    "en_US": MEDICAL_VARS
    + """<p>
                    <t t-out="partner.salutation"/>
                    <br/>
                    <br/>
                    Once again, thank you for your interest in Compassionate work for the benefit of children living in extreme poverty. We look forward to your journey <t t-out="event.country_id.in_preposition"/> <t t-out="event.country_id.name"/>. Thank you very much!
                    <br/>
                    <br/>
                    It is time to prepare the trip in terms of health. The stay that awaits you will be interesting. It can also be challenging: long international flights, jet lag, altitude changes, travel on rough roads, hiking on rough terrain and long days will be possible.
                    <br/>
                    <br/>
                    Because we know that every individual is different, we collect health information from each registrant to be aware of their limitations and specific needs.
                    <br/>
                    <br/>
                    Click here to review the checklist and make sure you are well prepared for this trip in terms of health:
                    <br/>
                    <br/>
                    </p>
                    """
    + _step1_button("base_url + survey.get_start_url()", "To the medical checklist")
    + """
<p>
                    Thank you for your commitment to children in need.
                    <br/>
                    <br/>
                    Receive our warmest greetings.
</p>
<t t-out="user.signature"/>""",
}

TRAVEL_VARS = """<t t-set="partner" t-value="object.partner_id"/>
<t t-set="registration" t-value="object.get_objects()"/>
<t t-set="event" t-value="registration.compassion_event_id"/>
<t t-set="payment_url" t-value="registration.payment_link"/>
<t t-set="user" t-value="registration.event_id.user_id"/>
"""
TRAVEL_BODY = {
    "fr_CH": TRAVEL_VARS
    + """<p>
   <t t-out="partner.salutation"/>
   <br/>
   <br/>
   Merci de votre engagement avec Compassion au profit des enfants vivant dans l'extrême pauvreté. Nous nous réjouissons de votre voyage.
   <br/>
   <br/>
   Il est temps de préparer le voyage sur le plan administratif. Cette étape devrait vous prendre 10 à 30 minutes. Vous serait-il possible de vous en charger dans les 15 jours à venir ?
  </p>
  <h2>
   1. Paiement du voyage
  </h2>
  <p>
  Ci-joint, vous trouverez la facture de ce voyage. Merci de la régler dans les 30 jours. Vous pouvez payer directement par carte de crédit&nbsp;ou à l'aide de bulletin de versement ci-joint. Si vous n'avez pas la possibilité de régler ce voyage en une seule fois, d'avance merci de prendre contact avec moi afin de trouver une solution ensemble (<t t-out="user.email"/>).
  </p>
  """
    + _step1_button("payment_url", "Paiement en ligne")
    + """
  <h2>
   2. Documents de voyage
  </h2>
  <h3>
   Assurance
  </h3>
   <p>
Compassion ne dispose pas d'assurance globale pour les participants aux voyages de parrains. Nous vous recommandons de contrôler la couverture de votre assurance maladie et accident. Une assurance annulation de voyage est vivement recommandée. En effet, une fois le billet d'avion acheté et en cas d'annulation, les frais seront à votre charge. Disposez-vous du
  <a href="https://www.tcs.ch/fr/produits/depannage-protection-voyage/assistance-voyage/livret-eti.php" style="color: skyblue; text-decoration: underline" title="">
   livret ETI Monde du TCS
  </a>
  ? Il s'agit d'une bonne assurance qui couvre les voyages à l'étranger et les annulations.
  <br/>
  <br/>
  Encore une fois, merci de votre engagement pour les enfants démunis.
  <br/>
  <br/>
  Recevez nos chaleureuses salutations.
   </p>
   <t t-out="user.signature"/>""",
    "de_DE": TRAVEL_VARS
    + """
    <p>
   <t t-out="partner.get('salutation').title()"/> <t t-out="partner.preferred_name"/>
   <br/>
   <br/>
   Danke für dein Interesse an der Arbeit von Compassion, durch die wir gemeinsam jeden Tag immer mehr Kinder aus extremer Armut befreien.
   <br/>
   <br/>
   Jetzt ist es Zeit für ein paar administrative Schritte in der Reisevorbereitung. 10 bis 30 Minuten reichen dafür. Wir möchten dich bitten, dass du dich in den kommenden zwei Wochen darum kümmerst.
  </p><h2>
   1. Bezahlung der Reise
  </h2>
<p>
  Beiliegend senden wir dir die Rechnung für die Reise. Danke, dass du sie innerhalb von 30 Tagen überweist. Du kannst direkt per Kreditkarte bezahlen (Link) oder mittels angehängtem Einzahlungsschein. Solltest du den Betrag nicht auf einmal bezahlen können, nimm doch bitte mit mir Kontakt auf, damit wir gemeinsam eine Lösung finden (<t t-out="user.email"/>)
</p>"""
    + _step1_button("payment_url", "Onlinezahlung")
    + """
<h2>
   2. Reisedokumente
  </h2>
  <h3>
Versicherung
  </h3>
<p>
 Compassion verfügt über keine Versicherung für die Teilnehmenden einer Reise. Wir empfehlen dir, den Deckungsbereich deiner Kranken- und Unfallversicherung abzuklären und ggf. eine Reiseannulationsversicherung abzuschliessen. Ist das Flugticket nämlich einmal gekauft und die Reise wird abgesagt, gehen die Kosten zu deinen Lasten. Hast du einen
  <a href="https://www.tcs.ch/de/produkte/pannenhilfe-reiseschutz/reiseschutz/eti-schutzbrief.php" style="color: skyblue; text-decoration: underline">
   TCS ETI Schutzbrief
  </a>
  ? Das ist eine gute Versicherungslösung, die Auslandreisen und Reiseannulationen abdeckt.
  <br/>
  <br/>
  Danke für dein Engagement für Kinder in Armut!
  <br/>
  <br/>
  Herzliche Grüsse
</p>
  <t t-out="user.signature"/>""",
    "en_US": TRAVEL_VARS
    + """
    <p>
    <t t-out="partner.salutation"/>
    <br/>
    <br/>
    Thank you for your commitment to Compassion for the benefit of children living in extreme poverty. We look forward to your journey  <t t-out="event.country_id.in_preposition"/> <t t-out="event.country_id.name"/>.
    <br/>
    <br/>
    It is time to prepare the trip administratively. This step should take you 10 to 30 minutes. Would you be able to do it within the next 15 days?
    <br/>
    <br/>
</p>
<h2>1. Payment of the trip</h2>
<p>
    Attached, you will find the invoice for this trip. Please pay it within 30 days. You can pay directly by credit card or Postfinance card or using the attached payment slip. If you do not have the possibility to pay for this trip in one go, please contact me in advance to find a solution together (rreber@compassion.ch).
</p>
"""
    + _step1_button("payment_url", "Online payment")
    + """
<h2>2. Travel documents</h2>
<h3>2.1. Passport</h3>
<p>Please check that your passport will be valid six months after the date of your planned return to Switzerland. If this is not the case, we ask you to renew your passport in order to guarantee you a worry-free trip.</p>
<h3>2.2. Insurance</h3>
<p>Compassion does not have comprehensive insurance for participants on sponsor trips. We recommend that you check your health and accident insurance coverage. Trip cancellation insurance is strongly recommended. Indeed, once the flight ticket has been purchased and in the event of cancellation, you will be responsible for the costs. Do you have the <a href="https://www.tcs.ch/fr/produits/depannage-protection-voyage/assistance-voyage/livret-eti.php" style="color:skyblue;text-decoration: underline">ETI World TCS booklet (click here)</a>? This is a good insurance that covers international travel and cancellations.</p>
<h3>2.4. Emergency contact</h3>
<p>Please make sure you informed your emergency contact about the trip. Here is the the emergency person you chose:</p>
<ul>
    <li>Name: <t t-out="registration.emergency_name"/></li>
    <li>Phone: <t t-out="registration.emergency_phone"/></li>
</ul>
<p>
    Once again, thank you for your commitment to children in need.
</p>
<p>
    Receive our warmest greetings.
</p>
<t t-out="user.signature"/>""",
}


@openupgrade.migrate()
def migrate(env, version):
    _swap_group_visit_xmlids(env)
    for xmlid, body, subject in (
        (
            STEP1_EMAIL_XMLID,
            STEP1_BODY,
            None,
        ),
        (
            "website_switzerland.group_visit_after_trip_feedback_email",
            FEEDBACK_BODY,
            FEEDBACK_SUBJECT,
        ),
        (
            "website_switzerland.group_visit_medical_survey_email",
            MEDICAL_BODY,
            None,
        ),
        (
            "website_switzerland.group_visit_travel_documents_email",
            TRAVEL_BODY,
            None,
        ),
    ):
        template = env.ref(xmlid, raise_if_not_found=False)
        if template:
            openupgrade.logged_query(
                env.cr,
                "UPDATE mail_template SET body_html = %s , subject = COALESCE(%s, subject) WHERE id = %s",
                (
                    json.dumps(body),
                    json.dumps(subject) if subject else None,
                    template.id,
                ),
            )
    env["mail.template"].invalidate_model(["body_html"])
    (
        env.ref("website_event_compassion.product_template_single_room")
        + env.ref("website_event_compassion.product_template_flight")
        + env.ref("website_event_compassion.product_template_trip_price")
        + env.ref("muskathlon.product_registration")
    ).write({"service_tracking": "event"})
    env.ref("website_switzerland.event_type_group_visit").write(
        {"stage_ids": [(4, env.ref("website_switzerland.stage_group_ready").id)]}
    )
