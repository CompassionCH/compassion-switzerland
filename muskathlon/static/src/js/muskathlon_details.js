odoo.define('muskathlon.muskathlon_details', function (require) {
    'use strict';

    var animation = require('web_editor.snippets.animation');

    animation.registry.muskathlon_details = animation.Class.extend({
        selector: "#muskathlon_details",
        start: function () {
            this.filter_sport_discipline();
        },
        filter_sport_discipline: function () {
            // Only allow selection of available disciplines for the Muskathlon registration form
            var disciplines = this.$("#available_disciplines li").map(function () { return $(this).val(); }).get();
            this.$("select[name='sport_discipline_id'] option").each(function (index, select_option) {
                var item = $(select_option);
                var value = item.val();
                if (value.length && disciplines.indexOf(parseInt(value)) < 0) {
                   item.remove();
                }
            });
        },
    });
});
