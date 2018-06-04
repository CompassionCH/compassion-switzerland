odoo.define('muskathlon.state_filter', function (require) {
    'use strict';

    var animation = require('web_editor.snippets.animation');

    animation.registry.state_filter = animation.Class.extend({
        selector: "#state_filter",
        start: function () {
            // Save all states
            this.el_state = $("form select[name*='state_id']");
            this.all_states = this.el_state.html();
            this.el_country = $("form select[name*='country_id']");

            // Filter states if country field is already set.
            this.filter_states();

            // Callback when country is changed
            var self = this;
            this.el_country.change(function () {
                // Restore all states
                self.el_state.parent().parent().show();
                self.el_state.empty();
                self.el_state.html(self.all_states);
                self.filter_states();
            });
        },
        filter_states: function() {
            // Filter states of forms
            var state_country = {};     // will hold state_id: country_id mapping
            this.$("li").each(function (index, li) {
                var element = $(li);
                state_country[parseInt(element.html())] = element.val();
            });
            var country_id = this.el_country.val();
            if (country_id != undefined) {
                this.el_state.children().each(function (index, select_option) {
                    var item = $(select_option);
                    var value = item.val();
                    if (value.length && state_country[value] != country_id) {
                       item.remove();
                    }
                });
            }
            if (this.el_state.children().length == 1) {
                this.el_state.parent().parent().hide();
            }
        }
    });
});
