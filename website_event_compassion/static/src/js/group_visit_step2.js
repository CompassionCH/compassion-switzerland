odoo.define('website_event_compassion.group_visit_step2', function (require) {
    'use strict';

    var animation = require('website.content.snippets.animation');

    animation.registry.group_visit_step2 = animation.Class.extend({
        selector: '#group_visit_step2',

        /**
         * Called when widget is started.
         */
        start: function () {
            this.scrollToOpenForm();
        },

        /**
         * Automatically scroll down to the opened form.
         */
        scrollToOpenForm: function () {
            var open_form = this.$('.in form');
            if (open_form.length) {
                $('html, body').animate({
                    scrollTop: open_form.offset().top,
                }, 1000);
            }
        },
    });
});
