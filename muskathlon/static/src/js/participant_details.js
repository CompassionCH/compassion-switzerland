odoo.define('muskathlon.participant_details', function (require) {
    'use strict';

    // Could be PROD or TEST
    var ENVIRONMENT = 'TEST';

    var animation = require('web_editor.snippets.animation');
    var Model = require('web.Model');
    var payment_acquirer = new Model('payment.acquirer');

    animation.registry.participant_details = animation.Class.extend({
        selector: ".o_participant_details",
        postURL: function(url, multipart) {
            var form = document.createElement("FORM");
            form.method = "POST";
            if(multipart) {
                form.enctype = "multipart/form-data";
            }
            form.style.display = "none";
            document.body.appendChild(form);
            form.action = url.replace(/\?(.*)/, function(_, urlArgs) {
                urlArgs.replace(/\+/g, " ").replace(/([^&=]+)=([^&=]*)/g, function(input, key, value) {
                    var data = document.createElement("INPUT");
                    data.type = "hidden";
                    data.name = decodeURIComponent(key);
                    data.value = decodeURIComponent(value);
                    form.appendChild(data);
                });
                return "";
            });
            form.submit();
        },
        start: function () {
            // get participant ID
            var url = window.location.href;
            var participant_id = parseInt(url.match("/participant/([0-9]+)-[A-z0-9\-%]+/")[1], 10);
            // get current event id
            var event_id = parseInt(url.match("/event/[A-z0-9\-]+-([0-9]+)/")[1], 10);

            var self = this;

            var payment_form = $('#payment_form');

            payment_form.attr('action', 'https://e-payment.postfinance.ch/ncol/' + ENVIRONMENT + '/orderstandard_utf8.asp');
            $('#donate_button').on('click', function(e) {
                // Serialize data function
                var objectifyFormFunc = function objectifyForm(formArray) {
                    var returnArray = {};
                    for (var i = 0; i < formArray.length; i++){
                        returnArray[formArray[i].name] = formArray[i].value;
                    }
                    return returnArray;
                };
                var data_json = objectifyFormFunc(payment_form.serializeArray());
                data_json.product_name = 'Muskathlon';
                data_json.ambassador = participant_id;
                data_json.event_id = event_id;
                payment_acquirer.call('create_invoice_and_payment_lines', [data_json]).then(function (res) {
                    self.postURL(res[0] + '?' + $.param(res[1]), false);
                }).fail(function (err) {
                    console.log('error', err); // eslint-disable-line no-console
                });
                e.preventDefault();
            });
        }
    });
});
