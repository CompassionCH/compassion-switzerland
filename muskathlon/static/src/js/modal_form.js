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
            var form_id = this.$el.attr("id");
            modal_form.submit(function (event) {
                // Prevent direct submission
                event.preventDefault();
                // Send form in ajax (remove translation url)
                var post_url = window.location.pathname;
                var form_data = self.$("form").serialize();
                $.post(post_url, form_data, function(render_result) {
                    var new_form = $(render_result).find("#" + form_id).find("form");
                    if (new_form.length) {
                        // The same page is returned, we must determine if we close the modal or not, based on errors.
                        if (new_form.find(".alert.alert-danger.error-msg").length) {
                            // We should replace the form content without closing the modal.
                            self.$el.find("form").html(new_form);
                            self.start();
                        } else {
                            // We can reload the page.
                            document.write(render_result);
                        }

                    } else {
                        // Another page is returned by the controller, we will display it inside the modal.
                        var payment_compassion = $(render_result).find('#payment_compassion');
                        if (payment_compassion.length) {
                            // Special case for payment form, we directly submit the payment form.
                            // Put the form inside the modal (but hide it), to allow form submission
                            self.$el.find(".modal-body").append(payment_compassion);
                            $("#payment_compassion").hide();
                            self.$el.find('#payment_compassion form').submit();
                        } else {
                            self.$el.find(".modal-body").html(render_result);
                        }
                    }

                })
                .fail(function() {
                    var message = _t("An error occurred during form submission. Please verify your submission or contact us in case of trouble.");
                    var formatted_mess = '<div id="server_error" class="alert alert-danger error-msg">' + message + '</div>';
                    var error_div = self.$el.find('#server_error');
                    if (error_div.length){
                        error_div.replace(formatted_mess);
                    } else {
                        self.$el.find('.above-controls').before(formatted_mess);
                    }
                })
            });
        }
    });
});
