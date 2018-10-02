odoo.define('muskathlon.muskathlon_details', function (require) {
    'use strict';

    var animation = require('web_editor.snippets.animation');

    animation.registry.muskathlon_details = animation.Class.extend({
        selector: '#muskathlon_details',

        /**
         * Called when widget is started.
         */
        start: function () {
            this.filter_sport_discipline();
        },

        /**
         * Only allow selection of available disciplines for the
         * Muskathlon registration form
         */
        filter_sport_discipline: function () {
            var disciplines = this.$('#available_disciplines li').map(
                function () {
                    return $(this).val();
                }).get();
            this.$('select[name=\'sport_discipline_id\'] option')
                .each(function (index, select_option) {
                    var item = $(select_option);
                    var value = item.val();
                    if (value.length && disciplines.indexOf(
                        parseInt(value, 10)) < 0) {
                        item.remove();
                    }
                });
        },
    });
});
