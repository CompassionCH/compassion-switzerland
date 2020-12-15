##############################################################################
#
#    Copyright (C) 2020 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import http
from odoo.addons.survey.controllers.main import Survey


class SurveyController(Survey):
    """
    Disable survey from sitemaps
    """

    @http.route(['/survey/start/<model("survey.survey"):survey>',
                 '/survey/start/<model("survey.survey"):survey>/<string:token>'],
                type='http', auth='public', website=True,
                sitemap=False)
    def start_survey(self, survey, token=None, **post):
        return super().start_survey(survey, token, **post)

    @http.route(['/survey/fill/<model("survey.survey"):survey>/<string:token>',
                 '/survey/fill/<model("survey.survey"):survey>/<string:token>/'
                 '<string:prev>'],
                type='http', auth='public', website=True,
                sitemap=False)
    def fill_survey(self, survey, token, prev=None, **post):
        return super().fill_survey(survey, token, prev, **post)

    @http.route(['/survey/prefill/<model("survey.survey"):survey>/<string:token>',
                 '/survey/prefill/<model("survey.survey"):survey>/<string:token>/'
                 '<model("survey.page"):page>'],
                type='http', auth='public', website=True, sitemap=False)
    def prefill(self, survey, token, page=None, **post):
        return super().prefill(survey, token, page, **post)

    @http.route(['/survey/scores/<model("survey.survey"):survey>/<string:token>'],
                type='http', auth='public', website=True, sitemap=False)
    def get_scores(self, survey, token, page=None, **post):
        return super().get_scores(survey, token, page, **post)

    @http.route(['/survey/results/<model("survey.survey"):survey>'],
                type='http', auth='user', website=True, sitemap=False)
    def survey_reporting(self, survey, token=None, **post):
        return super().survey_reporting(survey, token, **post)
