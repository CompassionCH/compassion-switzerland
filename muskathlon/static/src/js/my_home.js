odoo.define('muskathlon.my_home', function (require) {
    'use strict';

    $(function () {
        // TODO This was taken from payment/payment_form.js module, but apparently there could be a better way
        // of loading the widget into the view. We can see how this one will evolve maybe.
        $('#muskathlon_my_home').each(function () {
            var $elem = $(this);
            var form = new MuskathlonHome(null, $elem.data());
            form.attachTo($elem);
        });
    });

    return MuskathlonHome;
});
