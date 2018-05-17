odoo.define('muskathlon.payment', function (require) {
    'use strict';

    var animation = require('web_editor.snippets.animation');
    var ajax = require('web.ajax');

    animation.registry.payment = animation.Class.extend({
        selector: "#payment_compassion",
        // Serialize data function
        objectifyFormFunc: function objectifyForm(formArray) {
            var returnArray = {};
            for (var i = 0; i < formArray.length; i++){
                returnArray[formArray[i].name] = formArray[i].value;
            }
            return returnArray;
        },
        start: function () {
            // See https://github.com/odoo/odoo/blob/10.0/addons/website_sale/static/src/js/website_sale_payment.js#L15
            // for reference
            // When choosing an acquirer, display its Pay Now button
            var $payment = $("#payment_compassion");
            var self = this;
            $payment.on("click", "input[name='acquirer'], a.btn_payment_token", function (ev) {
                var ico_off = 'fa-circle-o';
                var ico_on = 'fa-dot-circle-o';

                var payment_id = $(ev.currentTarget).val() || $(this).data('acquirer');
                var token = $(ev.currentTarget).data('token') || '';

                $("div.oe_sale_acquirer_button[data-id='"+payment_id+"']", $payment).attr('data-token', token);
                $("div.js_payment a.list-group-item").removeClass("list-group-item-info");
                $('span.js_radio').switchClass(ico_on, ico_off, 0);
                if (token) {
                    $("div.oe_sale_acquirer_button div.token_hide").hide();
                    $(ev.currentTarget).find('span.js_radio').switchClass(ico_off, ico_on, 0);
                    $(ev.currentTarget).parents('li').find('input').prop("checked", true);
                    $(ev.currentTarget).addClass("list-group-item-info");
                }
                else{
                    $("div.oe_sale_acquirer_button div.token_hide").show();
                }
                $("div.oe_sale_acquirer_button[data-id]", $payment).addClass("hidden");
                $("div.oe_sale_acquirer_button[data-id='"+payment_id+"']", $payment).removeClass("hidden");

            })
                .find("input[name='acquirer']:checked").click();

            // When clicking on payment button: create the tx using json then continue to the acquirer
            $payment.on("click", 'button[type="submit"], button[name="submit"]', function (ev) {
                ev.preventDefault();
                ev.stopPropagation();
                var $form = $(ev.currentTarget).parents('form');
                var payment_form = $('#payment_form');
                var acquirer = $(ev.currentTarget).parents('div.oe_sale_acquirer_button').first();
                var acquirer_id = acquirer.data('id');
                var acquirer_token = acquirer.attr('data-token'); // !=data
                var params = self.objectifyFormFunc(payment_form.serializeArray());
                params.tx_type = acquirer.find('input[name="odoo_save_token"]').is(':checked')?'form_save':'form';
                if (! acquirer_id) {
                    return false;
                }
                if (acquirer_token) {
                    params.token = acquirer_token;
                }
                $form.off('submit');
                ajax.jsonRpc(payment_form.data('callback') + acquirer_id, 'call', params).then(function (data) {
                    $(data).appendTo('body').submit();
                }).fail(function (err, mess) {
                    $('.alert').show();
                    console.log('error', mess.name); // eslint-disable-line no-console
                });
                return false;
            });

            $('div.oe_pay_token').on('click', 'a.js_btn_valid_tx', function() {
                $('div.js_token_load').toggle();

                var $form = $(this).parents('form');
                ajax.jsonRpc($form.attr('action'), 'call', $.deparam($form.serialize())).then(function (data) {
                    if (data.url) {
                        window.location = data.url;
                    }
                    else {
                        $('div.js_token_load').toggle();
                        if (!data.success && data.error) {
                            $('div.oe_pay_token div.panel-body p').html(data.error + "<br/><br/>" + _('Retry ? '));
                            $('div.oe_pay_token div.panel-body').parents('div').removeClass('panel-info').addClass('panel-danger');
                        }
                    }
                });

            });
        }
    });
});