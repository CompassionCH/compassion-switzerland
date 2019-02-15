odoo.define('website_event_compassion.group_visit_registration_step1', function (require) {
    'use strict';

    var animation = require('web_editor.snippets.animation');

    animation.registry.group_visit_step1 = animation.Class.extend({
        selector: '.cms_form_group_visit_registration',

        /**
         * Called when widget is started.
         */
        start: function () {
            // Trigger on hide or show double room field based on room type selected
            var double_field_div = $('div.field-double_room_person');
            var radio_field = $('input[type=radio][name=single_double_room]');
            radio_field.change(function() {
                if (this.value == 'single') {
                    double_field_div.find('input').val('');
                    double_field_div.hide();
                }
                else if (this.value == 'double') {
                    double_field_div.show();
                }
            });
            // Hide the field if default value is single
            var checked_field = $('input[type=radio][name=single_double_room]:checked');
            if (checked_field.val() == 'single') {
                double_field_div.hide();
            }
        },
    });
});
