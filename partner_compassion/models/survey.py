##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Quentin Gigon <gigon.quentin@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models, fields, api


class SurveyQuestion(models.Model):
    _inherit = "survey.question"

    # when used this field tells the validation process that the maximum number of option answer should be validated
    max_checked_option = fields.Integer(
        help="if set, maximum number of options allowed for the user")

    @api.multi
    def validate_multiple_choice(self, post, answer_tag):
        # call super() function to avoid missing important behaviour
        errors = super().validate_multiple_choice(post=post, answer_tag=answer_tag)
        # add check for maximum number of answered option.
        if self.max_checked_option:
            # get answer candidate based on post dictionary
            answer_candidates = {k: v for k, v in post.items() if k.startswith(answer_tag)}
            if len(answer_candidates) > self.max_checked_option:
                errors.update({answer_tag: self.constr_error_msg})

        return errors


class SurveyLabel(models.Model):
    _inherit = "survey.label"

    order_in_question = fields.Integer(
        "Order of the question. Used in multiple options question when order is important. should starts at 0",
    )


class SurveyUserInput(models.Model):
    _inherit = "survey.user_input"

    def write(self, vals):
        out = super().write(vals)

        # compute segment affinity if needed
        is_done = vals.get("state") == "done"
        segment_survey = self.env.ref("partner_compassion.partner_segmentation_survey")

        for user_input in self:
            if user_input.survey_id == segment_survey and is_done:
                ans = self._get_answer_as_array()
                self.env["res.partner.segment.affinity"].segment_affinity_engine(ans, self.partner_id.id)

        return out

    def _get_answer_as_array(self):
        """
        Will transform a survey input into an array with input_line mark.
        Use mainly for segmentation computation with segmentation survey.
        :return: an array containing line_input marks
        """

        out = []
        all_options = {}

        # for each user input (one for simple_choice and multiple for multiple_choice) extract answer value as
        # store in quizz_mark.
        for user_input_line in self.user_input_line_ids:

            # with simple_choice type retrieving the answer is trivial
            if user_input_line.question_id.type == "simple_choice":
                out.append([user_input_line.quizz_mark])

            # multiple_choice require further steps. expected output (for a multiple_choice question) is an array with
            # 0 for unselected option and "quizz_mark" for selected option.
            elif user_input_line.question_id.type == "multiple_choice":

                q = user_input_line.question_id

                if q.id not in all_options:
                    # if this question as not been seen yet. create a 0 filled array with as many entry as label for
                    # this question (label = answering option). add the array to a dictionary to use it for
                    # user_input_line related to the same question.
                    all_options[q.id] = [0 for _ in self.env["survey.label"].search(
                        [("question_id", "=", q.id)])]

                    # when comment counts as an answer add a 0 to the array
                    if q.comments_allowed and q.comment_count_as_answer:
                        all_options[q.id].append(0)

                    # append the newly created array to the output. Further modification of the array will still
                    # affect the output by reference.
                    out.append(all_options[q.id])

                if q.comment_count_as_answer and user_input_line.answer_type == "text":
                    # if current input is user comment append a value of 1 at the end of the array (comment always at
                    # the end).
                    all_options[q.id][-1] = 1
                else:
                    # used the field "order_in_question" to store the input_line.quizz mark at the correct index.
                    all_options[q.id][user_input_line.value_suggested.order_in_question] = user_input_line.quizz_mark

        # Flatten the output before returning it.
        return [_input for answer in out for _input in answer]


class SurveyUserInputLine(models.Model):
    _inherit = "survey.user_input_line"

    partner_id = fields.Many2one(
        related="user_input_id.partner_id", store=True, readonly=False
    )
