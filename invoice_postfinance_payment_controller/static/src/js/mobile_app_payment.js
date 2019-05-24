odoo.define('mobile_app_payment_controller.mobile_payment', function (require) {
    'use strict';

    var animation = require('web_editor.snippets.animation');

    animation.registry.group_visit_step2 = animation.Class.extend({
        selector: '#mobile_app_payment_redirect',

        /**
         * Called when widget is started.
         */
        start: function () {
            var payment_status = this.$el.attr("class");
            if payment_status === 'ok' {
                window.location = "compassionappuk://";
            } else {
                window.location = "compassionappuk://CancelDDDonation";
            }
        }
    });
});
