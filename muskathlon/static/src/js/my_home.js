odoo.define('muskathlon.my_home', function (require) {
    'use strict';

    var Widget = require("web.Widget");

    var MuskathlonHome = Widget.extend({
        /**
         * Called when widget is started
         */
        start: function () {
            this.auto_submit_images();
        },

        /**
         * Submit and reload pictures in view
         */
        auto_submit_images: function () {
            this.$('#upload_picture_1, #upload_picture_2').change(function () {
                var form_id = $(this).prop('id').replace('upload', 'form');
                var content_id = form_id.replace('form', 'content');
                $.ajax({
                    url: '/my/api',
                    type: 'POST',
                    data: new FormData($('#' + form_id)[0]),
                    processData: false,
                    contentType: false,
                })
                    .done(function (data) {
                        if (!(/no image uploaded/).test(data)) {
                            $('#' + content_id).html(data);
                            $('#success_message').show();
                        }
                    });
            });
        },
    });

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
