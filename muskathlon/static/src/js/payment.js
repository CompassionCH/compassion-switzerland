odoo.define('muskathlon.payment', function (require) {
    'use strict';

    var animation = require('web_editor.snippets.animation');

    animation.registry.payment = animation.Class.extend({
        selector: "#payment_compassion",
        start: function () {
            // Automatically submit payment form
            var payment_form = $("form");
            payment_form.submit();
        }
    });
});
