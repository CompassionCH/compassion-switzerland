// openerp.sync_mail_multi_attach = function (session){
odoo.define('sync_mail_multi_attach.multi_attachments', function (require) {
    'use strict';

    var core = require('web.core');
    var _t = core._t;
    var composer = require('mail.composer');
    // var qweb = core.qweb;
    var FieldMany2ManyBinaryMultiFiles = core.form_widget_registry.get(
        'many2many_binary');

    composer.BasicComposer.include({
        // TODO: migrate download all attachments
        // render_attachments: function () {
        //     this._super.apply(this, arguments);
        //     this.$(".download-all-attachment").html(qweb.render(
        //          'download.all.attachment', {'widget': this}));
        // },

        /**
         * When attachment is changed
         * @param event
         * @returns {boolean}
         */
        on_attachment_change: function (event) {
            event.stopPropagation();
            var self = this;
            var $target = $(event.target);
            if ($target.val() !== '') {
                var filename = $target.val().replace(/.*[\\/]/, '');
                // if the files exits for this answer, delete the file before
                // upload
                var attachments = [];
                for (var i in this.get('attachment_ids')) {
                    if ((this.get('attachment_ids')[i].filename ||
                        this.get('attachment_ids')[i].name) === filename) {
                        if (this.get('attachment_ids')[i].upload) {
                            return false;
                        }
                        this.AttachmentDataSet.unlink([this.get(
                            'attachment_ids')[i].id]);
                    } else {
                        attachments.push(this.get('attachment_ids')[i]);
                    }
                }
                // submit filename
                this.$('form.o_form_binary_form').submit();
                this.$attachment_button.prop('disabled', true);
                this.set('attachment_ids', attachments);

                // submit other files
                _.each($target[0].files, function (file) {
                    var querydata = new FormData();
                    querydata.append('callback', 'o_fileupload_temp2');
                    querydata.append('ufile', file);
                    querydata.append('model', 'mail.compose.message');
                    querydata.append('id', '0');
                    querydata.append('multi', 'true');
                    querydata.append('csrf_token', core.csrf_token);
                    $.ajax({
                        url: '/web/binary/upload_attachment',
                        type: 'POST',
                        data: querydata,
                        cache: false,
                        processData: false,
                        contentType: false,
                        success: function (result) {
                            var data = JSON.parse(result);
                            attachments = self.get('attachment_ids');
                            attachments.push({
                                'id': data.id,
                                'name': file.name,
                                'filename': data.filename,
                                'url': '',
                                'upload': false,
                                'mimetype': data.mimetype
                            });
                            self.set('attachment_ids', attachments);
                        }
                    });

                });
            }
        }
    });

    FieldMany2ManyBinaryMultiFiles.extend({

        /**
         * When file is changed
         * @param event
         * @returns {boolean}
         */
        on_file_change: function (event) {
            event.stopPropagation();
            var self = this;
            var $target = $(event.target);
            if ($target.val() !== '') {
                var filename = $target.val().replace(/.*[\\/]/, '');
                // don't uplode more of one file in same time
                if (self.data[0] && self.data[0].upload) {
                    return false;
                }
                for (var id in this.get('value')) {
                    // if the files exits, delete the file before upload
                    // (if it's a new file)
                    if (self.data[id] && (self.data[id].filename ||
                        self.data[id].name) === filename &&
                        !self.data[id].no_unlink) {
                        self.ds_file.unlink([id]);
                    }
                }

                // block UI or not
                if (this.node.attrs.blockui > 0) {
                    $.blockUI();
                }

                // TODO : unactivate send on wizard and form
                _.each($target[0].files, function (file) {
                    var querydata = new FormData();
                    querydata.append('callback', 'o_fileupload_temp2');
                    querydata.append('ufile', file);
                    querydata.append('model', 'mail.compose.message');
                    querydata.append('id', '0');
                    querydata.append('multi', 'true');
                    querydata.append('csrf_token', core.csrf_token);
                    $.ajax({
                        url: '/web/binary/upload_attachment',
                        type: 'POST',
                        data: querydata,
                        cache: false,
                        processData: false,
                        contentType: false,
                        success: function (result) {
                            var data = JSON.parse(result);
                            self.data[id] = {
                                'id': data.id,
                                'name': file.name,
                                'filename': data.filename,
                                'url': '',
                                'upload': false,
                                'mimetype': data.mimetype
                            };
                        }
                    });

                });
                // submit file
                this.$('form.o_form_binary_form').submit();
            }
        },

        /**
         * When file is uploaded
         * @param event
         * @param result
         */
        on_file_loaded: function (event, result) {
            if (this.node.attrs.blockui > 0) {
                $.unblockUI();
            }

            if (result.error || !result.id) {
                this.do_warn(_t('Uploading Error'), result.error);
                delete this.data[0];
            } else {
                var values = [];
                _.each(this.data, function (file) {
                    values.push(file.id);
                });
                this.set({'value': values});
            }
            this.render_value();
        }
    });

});
