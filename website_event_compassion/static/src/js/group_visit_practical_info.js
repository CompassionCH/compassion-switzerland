odoo.define('website_event_compassion.practical_info', function (require) {
    'use strict';

    var animation = require('web_editor.snippets.animation');

    animation.registry.practical_info = animation.Class.extend({
        selector: '#group_visit_practical_info',

        /**
         * Called when widget is started.
         */
        start: function () {
            // Show the content based on the button clicked
            this.$("#meet-button").on("click", function() {
                $("#vertical-menu button").removeClass("btn-primary");
                $("#meet-button").addClass("btn-primary");
                $("#practical_content div").hide();
                $("#practical_content #meeting").show();
            });

            this.$("#program-button").on("click", function() {
                $("#vertical-menu button").removeClass("btn-primary");
                $("#program-button").addClass("btn-primary");
                $("#practical_content div").hide();
                $("#practical_content #programs").show();
            });

            this.$("#health-button").on("click", function() {
                $("#vertical-menu button").removeClass("btn-primary");
                $("#health-button").addClass("btn-primary");
                $("#practical_content div").hide();
                $("#practical_content #health").show();
            });

            this.$("#luggage-button").on("click", function() {
                $("#vertical-menu button").removeClass("btn-primary");
                $("#luggage-button").addClass("btn-primary");
                $("#practical_content div").hide();
                $("#practical_content #luggage").show();
            });
        },
    });
});
