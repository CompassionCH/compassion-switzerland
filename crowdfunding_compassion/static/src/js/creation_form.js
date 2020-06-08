odoo.define('crowdfunding_compassion.creation_form', function (require) {
    'use strict';

    var animation = require('website.content.snippets.animation');
    var core = require('web.core');
    var _t = core._t;

    animation.registry.crowdfunding_creation_form = animation.Class.extend({
        selector: '.crowdfunding_project_creation_from',

        /**
         * Called when widget is started.
         */
        start: function () {
            $("[id^=product-choose-]").click(function () {
                // Show the product settings
                var button_id = this.getAttribute("id");
                var id_array = button_id.split("-");
                var product_index = id_array[id_array.length - 1];
                $("[id^=fund-settings-]").hide();
                $("#fund-settings-" + product_index).show();
                // Copy product_id to real form
                var product_id = $("#product-id-" + product_index).val();
                $("#product_id").val(product_id);
            });

            $("[id^=fund-number-]").change(function () {
                // Copy fund amount to real form
                $("#participant_product_number_goal").val($(this).val());
            });

            $("#number-sponsorships").change(function () {
                // Copy sponsorship goal to real form
                $("#participant_number_sponsorships_goal").val($(this).val());
            });

            // Hide required fields legend
            $(".above-controls").hide();

            // Show the correct social media help text depending on the project type
            $("select#type").change(function () {
                var value = $(this).val();
                var help = $("#social_medias .fieldset-description");
                var web_label = $("label[for=personal_web_page_url]");
                var web_input = $("input#personal_web_page_url");
                if (value === "individual") {
                    help.html(_t("If you have any social media account that you use to promote your project, you can link them to your personal page."));
                    var web_text = _t("Personal web page");
                    web_label.html(web_text);
                    web_input.attr("placeholder", web_text);
                } else {
                    help.html(_t(
                    "If there is any social media pages for your event, you can link them on the project page. Please don't put any personal profiles here. " +
                    "You will be able to put your personal social media accounts in the last step."));
                    var web_text = _t("Project web page");
                    web_label.html(web_text);
                    web_input.attr("placeholder", web_text);
                }
            });
        }
    });

    return animation.registry.crowdfunding_creation_form;
});
