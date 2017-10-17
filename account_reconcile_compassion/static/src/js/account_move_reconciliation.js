/* This is Javascript extension of module account
   in order to add custom reconcile buttons in the 
   Manual Reconcile view */
odoo.define('account_reconcile_compassion.reconciliation', function (require) {
    "use strict";

    var core = require('web.core');
    var reconciliation = require('account.reconciliation');
    var _t = core._t;
    var FieldMany2One = core.form_widget_registry.get('many2one');
    var FieldChar = core.form_widget_registry.get('char');
    var Model = require('web.Model');

    // Extend the class written in module account (bank statement view)
    reconciliation.bankStatementReconciliationLine.include({
        events: _.extend({
            // // TODO : this removes the ability to change partner of a line
            // //        but this functionality may not be necessary for us.
            "click .partner_name": "open_partner"
        }, reconciliation.bankStatementReconciliationLine.prototype.events),

        open_partner: function() {
            this.do_action({
                views: [[false, 'form']],
                view_type: 'form',
                view_mode: 'form',
                res_model: 'res.partner',
                type: 'ir.actions.act_window',
                target: 'current',
                res_id: this.partner_id
            });
        },

        // Set domain of sponsorship field and auto-find sponsorship for gift payments
        initializeCreateForm: function() {
            var self = this;
            _.each(self.create_form, function(field) {
                if (field.name === 'sponsorship_id') {
                    field.field.domain = ['|', '|', ['partner_id', '=', self.partner_id], ['partner_id.parent_id', '=', self.partner_id], ['correspondant_id', '=', self.partner_id], ['state', '!=', 'draft']];
                }
            });
            this._super();

            var line_name = self.st_line.name;
            var child_gift_match = line_name.match(/\[.+\]/);
            if (child_gift_match) {
                // Search Gift Product
                var gift_name = line_name.replace(child_gift_match[0], "");
                var product_obj = new Model("product.product");
                var product_search = [['name', 'like', gift_name]];
                $.when(product_obj.call("search", [product_search])).then(function(product_ids){
                    if (product_ids) {
                        self.product_id_field.set_value(product_ids[0]);
                    }
                });

                // Search sponsorship
                var child_code = child_gift_match[0].replace("[", "").replace("]", "").match(/\w+/)[0];
                var sponsorship_obj = new Model("recurring.contract");
                var sponsorship_search = [['child_code', 'like', child_code], ['partner_id', '=', self.st_line.partner_id]];
                $.when(sponsorship_obj.call("search", [sponsorship_search])).then(function(sponsorship_ids){
                    if (sponsorship_ids) {
                        self.sponsorship_id_field.set_value(sponsorship_ids[0]);
                    }
                });
            }

            // Store product selected
            this.product_selected = false;
        },

        // Return values of new fields to python.
        prepareCreatedMoveLinesForPersisting: function(lines) {
            var result = this._super(lines);
            for (var i = 0; i < result.length; i++) {
                if (lines[i].product_id) {
                    result[i].product_id = lines[i].product_id;
                }
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

        // Update fields when product_id is changed.
        createdLinesChanged: function() {
            this._super();
            var model_presets = new Model("account.reconcile.model");
            var self = this;
            var product_id = self.product_id_field.get_value("product_id");
            if (product_id != this.product_selected) {
                this.product_selected = product_id;
                model_presets.call("product_changed", [product_id]).then(function(values) {
                    if (values) {
                        self.account_id_field.set_value(values.account_id);
                        self.analytic_account_id_field.set_value(values.analytic_id);
                    }
                });
            }
        }
    });

    reconciliation.abstractReconciliation.include({
        // Add fields in reconcile view
        init: function(parent, context) {
            this._super(parent, context);

            // Extend an arbitrary field/widget with an init function that
            // will set the options attribute to a given object.
            // This is useful to pass arguments for a field when using the
            // web_m2x_options module.
            function fieldWithOptions(fieldClass, options) {
                return fieldClass.extend({
                    // pylint: disable=W7903
                    init: function() {
                        this._super.apply(this, arguments);
                        this.options = options;
                    }
                });
            }

            this.create_form_fields.product_id = {
                id: "product_id",
                index: 5,
                corresponding_property: "product_id",
                label: _t("Product"),
                required: false,
                tabindex: 15,
                constructor: FieldMany2One,
                field_properties: {
                    relation: "product.product",
                    string: _t("Product"),
                    type: "many2one"
                }
            };
            this.create_form_fields.sponsorship_id = {
                id: "sponsorship_id",
                index: 6,
                corresponding_property: "sponsorship_id",
                label: _t("Sponsorship"),
                required: false,
                tabindex: 16,
                constructor: fieldWithOptions(FieldMany2One,
                    {
                        'field_color': 'state',
                        'colors': {'cancelled': 'gray', 'terminated': 'gray',
                                   'mandate': 'red', 'waiting': 'green'},
                        'create': false,
                        'create_edit': false
                    }),
                field_properties: {
                    relation: "recurring.contract",
                    string: _t("Sponsorship"),
                    type: "many2one"
                }
            };
            this.create_form_fields.user_id = {
                id: "user_id",
                index: 7,
                corresponding_property: "user_id",
                label: _t("Ambassador"),
                required: false,
                tabindex: 17,
                constructor: FieldMany2One,
                field_properties: {
                    relation: "res.partner",
                    string: _t("Ambassador"),
                    type: "many2one"
                }
            };
            this.create_form_fields.comment = {
                id: "comment",
                index: 7,
                corresponding_property: "comment",
                label: _t("Gift Instructions"),
                required: false,
                tabindex: 17,
                constructor: FieldChar,
                field_properties: {
                    string: _t("Gift Instructions"),
                    type: "char"
                }
            };
        },

        // Add product_id to statement operations.
        fetchPresets: function() {
            var self = this;
            return this._super().then(function() {
                self.model_presets.query().order_by('-sequence', '-id').all().then(function (data) {
                    _(data).each(function(datum){
                        self.presets[datum.id].lines[0].product_id = datum.product_id;
                    });
                });
            });

        },

        // Change behaviour when clicking on name of bank statement
        statementNameClickHandler: function() {
            this.do_action({
                views: [[false, 'form']],
                view_type: 'form',
                view_mode: 'form',
                res_model: 'account.bank.statement',
                type: 'ir.actions.act_window',
                target: 'current',
                res_id: this.statement_ids[0]
            });
        }

    });
});
