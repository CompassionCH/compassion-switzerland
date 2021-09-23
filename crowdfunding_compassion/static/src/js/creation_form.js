odoo.define('crowdfunding_compassion.creation_form', function (require) {
    'use strict';

    var animation = require('website.content.snippets.animation');

    animation.registry.crowdfunding_creation_form = animation.Class.extend({
        selector: '.crowdfunding_project_creation_from',

        /**
         * Called when widget is started.
         */
        start: function () {
            // limit the number of characters of campaign name
            if ($("#campaign_name").length) {
                const MAX_CAMPAIGN_NAME_LEN = 100;
                // create div element and insert number of characters written
                var count_div = document.createElement("div");
                count_div.style.cssText = 'text-align:right';
                count_div.setAttribute("id", "count_div");
                var count_text = $("#campaign_name").val().length+"/"+MAX_CAMPAIGN_NAME_LEN;
                var count_text_node = document.createTextNode(count_text);
                count_div.appendChild(count_text_node);
                $("#campaign_name").after(count_div);
                // handle number of characters at keypress
                $("#campaign_name").on("keydown keyup", function (e) {
                    var campaign_name = $(this).val();
                    var len = campaign_name.length;
                    if (len > MAX_CAMPAIGN_NAME_LEN && e.keyCode !== 8 && e.keyCode !== 46
                    && e.keyCode !== 37 && e.keyCode !== 39) {
                        e.preventDefault();
                        var res = campaign_name.substring(0, MAX_CAMPAIGN_NAME_LEN);
                        $(this).val(res);
                    } else {
                        $("#count_div").html(len+"/"+MAX_CAMPAIGN_NAME_LEN);
                    }
                });
            }

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

            // If the number of participant is set, it should appear in the corresponding widget
            if ($("#participant_product_number_goal").val()) {
                $("[id^=fund-number-]").val($("#participant_product_number_goal").val());
            }

            $("[id^=fund-number-]").change(function () {
                // Copy fund amount to real form
                $("#participant_product_number_goal").val($(this).val());
            });

            // If the number of sponsorship is set, it should appear in the corresponding widget
            if ($("#participant_number_sponsorships_goal").val()) {
                $("#number-sponsorships").val($("#participant_number_sponsorships_goal").val());
            }

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
                    help.html($("#individual_media_help").text());
                    var web_text = $("#individual_url_help").text();
                    web_label.html(web_text);
                    web_input.attr("placeholder", web_text);
                } else {
                    help.html($("#collective_media_help").text());
                    var web_text = $("#collective_url_help").text();
                    web_label.html(web_text);
                    web_input.attr("placeholder", web_text);
                }
            });

            $("form").submit(function () {
                // prevent duplicate form submissions
                $(this).find(":submit").attr('disabled', 'disabled');
            });
        }
    });

    return animation.registry.crowdfunding_creation_form;
});
