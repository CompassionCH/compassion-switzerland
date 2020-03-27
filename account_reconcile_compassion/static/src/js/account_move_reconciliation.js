/* This is Javascript extension of module account
   in order to add custom reconcile buttons in the
   Manual Reconcile view */

// TODO CO-3190 Migrate this JS !
odoo.define('account_reconcile_compassion.reconciliation', function (require) {
    'use strict';

    var core = require('web.core');
    var reconciliation = require(
        'account_reconcile_create_invoice.reconciliation');
    var _t = core._t;
    var FieldMany2One = core.form_widget_registry.get('many2one');
    var FieldChar = core.form_widget_registry.get('char');
    var rpc = require('web.rpc');

    // Extend the class written in module account (bank statement view)
    reconciliation.bankStatementReconciliationLine.include({

        /**
         * Set domain of sponsorship field and auto-find sponsorship for
         * gift payments
         */
        initializeCreateForm: function () {
            var self = this;
            _.each(self.create_form, function (field) {
                if (field.name === 'sponsorship_id') {
                    field.field.domain = [
                        '|', '|', ['partner_id', '=', self.partner_id],
                        ['partner_id.parent_id', '=', self.partner_id],
                        ['correspondent_id', '=', self.partner_id],
                        ['state', '!=', 'draft'],
                    ];
                }
            });
            this._super();

            var line_name = self.st_line.name;
            var child_gift_match = line_name.match(/\[.+\]/);
            if (child_gift_match) {
                // Search Gift Product
                var gift_name = line_name.replace(child_gift_match[0], '');
                rpc.query({
                     model: 'product.product',
                     method: 'search',
                     args: [{
                        'name': gift_name,
                    }]
                }).then(function(product_ids){
                     if (product_ids !== 'undefined' &&
                        product_ids.length > 0) {
                        self.product_id_field.set_value(product_ids[0]);
                    }
                });
//                var product_obj = new Model('product.product');
//                var product_search = [['name', 'like', gift_name]];
//                $.when(product_obj.call('search', [product_search])).then(
//                    function (product_ids) {
//                        if (product_ids !== 'undefined' &&
//                            product_ids.length > 0) {
//                            self.product_id_field.set_value(product_ids[0]);
//                        }
//                    });

                // Search sponsorship
                var child_code = child_gift_match[0].replace('[', '').replace(
                    ']', '').match(/\w+/)[0];
                rpc.query({
                     model: 'recurring.contract',
                     method: 'search',
                     args: [{
                        'child_code': child_code,
                        'correspondent_id': self.st_line.partner_id,
                        'partner_id': self.st_line.partner_id,
                    }]
                }).then(function(sponsorship_ids){
                    if (typeof sponsorship_ids !== 'undefined' &&
                    sponsorship_ids.length > 0) {
                        self.sponsorship_id_field.set_value(
                            sponsorship_ids[0]);
                    }
                });
//                var sponsorship_obj = new Model('recurring.contract');
//                var sponsorship_search = [
//                    ['child_code', 'like', child_code],
//                    '|',
//                    ['correspondent_id', '=', self.st_line.partner_id],
//                    ['partner_id', '=', self.st_line.partner_id],
//                ];
//                $.when(sponsorship_obj.call('search', [sponsorship_search]))
//                    .then(function (sponsorship_ids) {
//                        if (typeof sponsorship_ids !== 'undefined' &&
//                        sponsorship_ids.length > 0) {
//                            self.sponsorship_id_field.set_value(
//                                sponsorship_ids[0]);
//                        }
//                    });
            }

            // Store product selected
            this.product_selected = false;
        },

        // Return values of new fields to python.
        prepareCreatedMoveLinesForPersisting: function (lines) {
            var result = this._super(lines);
            for (var i = 0; i < result.length; i++) {
                if (lines[i].sponsorship_id) {
                    result[i].sponsorship_id = lines[i].sponsorship_id;
                }
                if (lines[i].user_id) {
                    result[i].user_id = lines[i].user_id;
                }
                if (lines[i].comment) {
                    result[i].comment = lines[i].comment;
                }
            }
            return result;
        },
    });

    reconciliation.abstractReconciliation.include({

        init: function (parent, context) {
            this._super(parent, context);

            // Extend an arbitrary field/widget with an init function that
            // will set the options attribute to a given object.
            // This is useful to pass arguments for a field when using the
            // web_m2x_options module.
            function fieldWithOptions (fieldClass, options) {
                return fieldClass.extend({
                    init: function () {
                        this._super.apply(this, arguments);
                        this.options = options;
                    },
                });
            }

            this.create_form_fields.sponsorship_id = {
                id: 'sponsorship_id',
                index: 6,
                corresponding_property: 'sponsorship_id',
                label: _t('Sponsorship'),
                required: false,
                tabindex: 16,
                constructor: fieldWithOptions(FieldMany2One,
                    {
                        'field_color': 'state',
                        'colors': {'cancelled': 'gray',
                            'terminated': 'gray',
                            'mandate': 'red',
                            'waiting': 'green'},
                        'create': false,
                        'create_edit': false,
                    }),
                field_properties: {
                    relation: 'recurring.contract',
                    string: _t('Sponsorship'),
                    type: 'many2one',
                },
            };
            this.create_form_fields.user_id = {
                id: 'user_id',
                index: 7,
                corresponding_property: 'user_id',
                label: _t('Ambassador'),
                required: false,
                tabindex: 17,
                constructor: FieldMany2One,
                field_properties: {
                    relation: 'res.partner',
                    string: _t('Ambassador'),
                    type: 'many2one',
                },
            };
            this.create_form_fields.comment = {
                id: 'comment',
                index: 7,
                corresponding_property: 'comment',
                label: _t('Gift Instructions'),
                required: false,
                tabindex: 17,
                constructor: FieldChar,
                field_properties: {
                    string: _t('Gift Instructions'),
                    type: 'char',
                },
            };
        },
    });
});
