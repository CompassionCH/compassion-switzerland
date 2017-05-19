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
            "click .partner_name": "open_partner",
        }, reconciliation.bankStatementReconciliationLine.prototype.events),
        
        open_partner: function() {
            this.do_action({
                views: [[false, 'form']],
                view_type: 'form',
                view_mode: 'form',
                res_model: 'res.partner',
                type: 'ir.actions.act_window',
                target: 'current',
                res_id: this.partner_id,
            });
        },

        // Capture when product is selected to put the corresponding account and analytic account.
        formCreateInputChanged: function(elt, val) {
            var line_created_being_edited = this.get("line_created_being_edited");
            var self = this;

            if (elt === this.product_id_field) {
                var product_id = elt.get("value");
                $.when(self.model_bank_statement_line.call("product_id_changed", [product_id, self.st_line.date])).then(function(data){
                    self.account_id_field.set_value(data['account_id']);
                    self.analytic_account_id_field.set_value(data['analytic_id']);
                });
            }

            this._super(elt, val);
        },
        
        // Set domain of sponsorship field and auto-find sponsorship for gift payments
        initializeCreateForm: function() {
            var self = this;
            _.each(self.create_form, function(field) {
                if (field.name == 'sponsorship_id') {
                    field.field.domain = ['|', '|', ['partner_id', '=', self.partner_id], ['partner_id.parent_id', '=', self.partner_id], ['correspondant_id', '=', self.partner_id], ['state', '!=', 'draft']]
                }
            });
            this._super()

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
        },

        // Return values of new fields to python.
        prepareCreatedMoveLinesForPersisting: function(lines) {
            var result = this._super(lines);
            for (var i = 0; i < result.length; i++) {
                if (lines[i].product_id) result[i]['product_id'] = lines[i].product_id;
                if (lines[i].sponsorship_id) result[i]['sponsorship_id'] = lines[i].sponsorship_id;
                if (lines[i].user_id) result[i]['user_id'] = lines[i].user_id;
                if (lines[i].comment) result[i]['comment'] = lines[i].comment;
            }
            return result;
        },
    });

    reconciliation.bankStatementReconciliation.include({
        events: _.extend({
            "click .button_do_all": "reconcileAll",
        }, reconciliation.bankStatementReconciliation.prototype.events),

        // Add fields in reconcile view
        init: function(parent, context) {
            this._super(parent, context);

            // Extend an arbitrary field/widget with an init function that
            // will set the options attribute to a given object.
            // This is useful to pass arguments for a field when using the
            // web_m2x_options module.
            function fieldWithOptions(fieldClass, options)
            {
                return fieldClass.extend({
                    init: function() {
                        this._super.apply(this, arguments);
                        this.options = options;
                    },
                });
            }

            this.create_form_fields["product_id"] = {
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
                    type: "many2one",
                }
            };
            this.create_form_fields["sponsorship_id"] = {
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
                        'create_edit': false,
                    }),
                field_properties: {
                    relation: "recurring.contract",
                    string: _t("Sponsorship"),
                    type: "many2one",
                },
            };
            this.create_form_fields["user_id"] = {
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
                    type: "many2one",
                }
            };
            this.create_form_fields["comment"] = {
                id: "comment",
                index: 7,
                corresponding_property: "comment",
                label: _t("Gift Instructions"),
                required: false,
                tabindex: 17,
                constructor: FieldChar,
                field_properties: {
                    string: _t("Gift Instructions"),
                    type: "char",
                }
            };
        },

        // Add product_id to statement operations.
        fetchPresets: function() {
            var self = this;
            return this._super().then(function() {
                self.model_presets.query().order_by('-sequence', '-id').all().then(function (data) {
                    _(data).each(function(datum){
                        self.presets[datum.id].lines[0]['product_id'] = datum.product_id
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
                res_id: this.statement_ids[0],
            });
        },

        reconcileAll: function() {
            this.reconcile_all = true;
            var reconciliations = _.filter(this.getChildren(), function(o) { return o.get("balance").toFixed(3) === "0.000"; })
            this.persistReconciliations(reconciliations);
        },

        displayReconciliations: function(number) {
            var self = this;
            return this._super(number).done(function() {
                var reconciliations = _.filter(self.getChildren(), function(o) { return o.get("balance").toFixed(3) === "0.000"; })
                if (self.reconcile_all && reconciliations.length > 0) {
                    self.persistReconciliations(reconciliations);
                } else {
                    self.reconcile_all = false;
                }
            });
        },
    });

    // Extend the class written in module account (manual reconcile)
    // reconciliation.ReconciliationListView.include({
    //     init: function() {
    //         this._super.apply(this, arguments);
    //         var self = this;
    //         // Enable or disable buttons based on number of lines selected
    //         this.on('record_selected', this, function() {
    //             if (self.get_selected_ids().length === 0) {
    //                 self.$(".oe_account_recon_reconcile").attr("disabled", "");
    //             } else {
    //                 self.$(".oe_account_recon_reconcile").removeAttr("disabled");
    //             }
    //             if (self.get_selected_ids().length < 2) {
    //                 self.$(".oe_account_recon_reconcile_fund").attr("disabled", "");
    //                 self.$(".oe_account_recon_reconcile_split").attr("disabled", "");
    //             } else {
    //                 self.$(".oe_account_recon_reconcile_fund").removeAttr("disabled");
    //                 self.$(".oe_account_recon_reconcile_split").removeAttr("disabled");
    //             }
    //         });
    //     },
    //
    //     load_list: function() {
    //         var self = this;
    //         var tmp = this._super.apply(this, arguments);
    //         if (this.partners) {
    //             // Add the buttons of reconciliation
    //             this.$(".oe_account_recon_reconcile").after(QWeb.render("AccountReconciliationCompassion", {widget: this}));
    //             this.$(".oe_account_recon_next").after(QWeb.render("AccountReconciliationOpenPartner", {widget: this}));
    //
    //             // Add listeners to button clicks and open the corresponding wizard
    //             this.$(".oe_account_recon_reconcile_fund").click(function() {
    //                 self.reconcile_fund();
    //             });
    //             this.$(".oe_account_recon_reconcile_split").click(function() {
    //                 self.reconcile_split();
    //             });
    //             this.$(".oe_account_recon_open_partner").click(function() {
    //                 self.open_partner();
    //             });
    //         }
    //
    //         return tmp;
    //     },
    //     reconcile_fund: function() {
    //         this.reconcile_custom_wizard("action_reconcile_fund_wizard")
    //     },
    //     reconcile_split: function() {
    //         this.reconcile_custom_wizard("action_reconcile_split_payment_wizard")
    //     },
    //     reconcile_custom_wizard: function(action_wizard){
    //         var self = this;
    //         var ids = this.get_selected_ids();
    //         if (ids.length < 2) {
    //             instance.web.dialog($("<div />").text(_t("You must choose at least two records.")), {
    //                 title: _t("Warning"),
    //                 modal: true
    //             });
    //             return false;
    //         }
    //
    //         new instance.web.Model("ir.model.data").call("get_object_reference", ["account_reconcile_compassion", action_wizard]).then(function(result) {
    //             var additional_context = _.extend({
    //                 active_id: ids[0],
    //                 active_ids: ids,
    //                 active_model: self.model
    //             });
    //             return self.rpc("/web/action/load", {
    //                 action_id: result[1],
    //                 context: additional_context
    //             }).done(function (result) {
    //                 result.context = instance.web.pyeval.eval('contexts', [result.context, additional_context]);
    //                 result.flags = result.flags || {};
    //                 result.flags.new_window = true;
    //                 return self.do_action(result, {
    //                     on_close: function () {
    //                         // Refresh the Manual Reconcile View after wizard is closed
    //                         self.do_search(self.last_domain, self.last_context, self.last_group_by);
    //                     }
    //                 });
    //             });
    //         });
    //     },
    //
    //     open_partner : function() {
    //         this.do_action({
    //             views: [[false, 'form']],
    //             view_type: 'form',
    //             view_mode: 'form',
    //             res_model: 'res.partner',
    //             type: 'ir.actions.act_window',
    //             target: 'current',
    //             res_id: this.partners[this.current_partner][0],
    //         });
    //     }
    //
    // });
});
