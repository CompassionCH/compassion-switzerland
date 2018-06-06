odoo.define('muskathlon.modal_form', function (require) {
    'use strict';

    var animation = require('web_editor.snippets.animation');
    var core = require('web.core');
    var _t = core._t;

    animation.registry.modal_form = animation.Class.extend({
        selector: ".cms_modal_form",
        start: function () {
            // Submit form in Javascript in order to render result inside the modal
            var modal_form = this.$("form");
            var self = this;
            this.form_id = this.$el.attr("id");
            modal_form.submit(function (event) {
                // Prevent direct submission
                event.preventDefault();
                // Send form in ajax (remove translation url)
                var post_url = window.location.pathname;
                var form_data = self.$("form").serialize();
                // Inject form name in data to help the controller know which form is submitted,
                // in case several modals are present.
                form_data += "&form_id=" + self.form_id;
                $.ajax({
                    type: "POST",
                    url: post_url,
                    data: form_data,
                    success: function (data) {
                        if (data.redirect) {
                            var result_html = $('<div></div>');
                            result_html.load(data.redirect, function() {
                               var payment_compassion = result_html.find('#payment_compassion');
                               if (payment_compassion.length) {
                                   // Special case for payment form, we directly submit the payment form.
                                   var modal_body = self.$el.find(".modal-body");
                                   modal_body.html(result_html.html());
                                   modal_body.find('#payment_compassion form').submit();
                               } else {
                                   self.on_receive_back_html_result(result_html.html());
                               }
                            });
                        } else {
                            self.on_receive_back_html_result(data);
                        }
                    },
                    error: function (data) {
                        // HTML page is sent back as error (because it's not JSON)
                        if (data.status === 200) {
                            self.on_receive_back_html_result(data.responseText);
                        } else {
                            var message = _t("An error occurred during form submission. Please verify your submission or contact us in case of trouble.");
                            var formatted_mess = '<div id="server_error" class="alert alert-danger error-msg">' + message + '</div>';
                            var error_div = self.$el.find('#server_error');
                            if (error_div.length) {
                                error_div.replace(formatted_mess);
                            } else {
                                self.$el.find('.above-controls').before(formatted_mess);
                            }
                        }
                    }
                });
            });
        },
        on_receive_back_html_result: function(render_result) {
            var new_form = $(render_result).find("#" + this.form_id).find("form");
            if (new_form.length) {
                // The same page is returned, we must determine if we close the modal or not, based on errors.
                if (new_form.find(".alert.alert-danger.error-msg").length) {
                    // We should replace the form content without closing the modal.
                    this.$el.find("form").html(new_form);
                    this.start();
                } else {
                    // We can reload the page.
                    document.write(render_result);
                }
            } else {
                // This is another page. we load it inside the modal.
                this.$el.find(".modal-body").html(render_result);
            }
        }
    });
});
