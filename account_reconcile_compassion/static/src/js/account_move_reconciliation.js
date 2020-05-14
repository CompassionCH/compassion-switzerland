/* This is Javascript extension of module account
   in order to add custom reconcile buttons in the
   Manual Reconcile view */
   // TODO CO-3189
odoo.define('account_reconcile_create_invoice.reconciliation', function (require) {
    "use strict";

    var core = require('web.core');
    var basic_fields = require('web.basic_fields');
    var relational_fields = require('web.relational_fields');
    var reconciliation_renderer = require('account.ReconciliationRenderer');
    var reconciliation_model = require('account.ReconciliationModel');
    var qweb = core.qweb;
    var _t = core._t;

    reconciliation_renderer.StatementRenderer.include({
        events: _.extend({}, reconciliation_renderer.StatementRenderer.prototype.events, {
            "click div:first h1.statement_name": "statementNameClickHandler"
        }),

        // Change behaviour when clicking on name of bank statement
        statementNameClickHandler: function() {
            this.do_action({
                views: [[false, 'form']],
                view_type: 'form',
                view_mode: 'form',
                res_model: 'account.bank.statement',
                type: 'ir.actions.act_window',
                target: 'current',
                res_id: this.model.bank_statement_id.id
            });
        }
    });

    // Extend the class written in module account (bank statement view)
    reconciliation_renderer.LineRenderer.include({

      // Overload of the default function in 'account.ReconciliationRenderer' which adds the product_id field. 
      // It doesn't seem possible to call the superclass function and then add the field as basic_model.js 
      // doesn't have a method to add fields to an existing record, only makeRecord.
       _renderCreate: function (state) {
          var self = this;
          this.model.makeRecord('account.bank.statement.line', [{
              relation: 'account.account',
              type: 'many2one',
              name: 'account_id',
              domain: [['company_id', '=', state.st_line.company_id], ['deprecated', '=', false]],
          }, {
              relation: 'account.journal',
              type: 'many2one',
              name: 'journal_id',
              domain: [['company_id', '=', state.st_line.company_id]],
          }, {
              relation: 'account.tax',
              type: 'many2one',
              name: 'tax_id',
              domain: [['company_id', '=', state.st_line.company_id]],
          }, {
              relation: 'account.analytic.account',
              type: 'many2one',
              name: 'analytic_account_id',
          }, {
              relation: 'account.analytic.tag',
              type: 'many2many',
              name: 'analytic_tag_ids',
          }, {
              type: 'boolean',
              name: 'force_tax_included',
          }, {
              type: 'char',
              name: 'label',
          }, {
              type: 'float',
              name: 'amount',
          }, {
              type: 'char', //TODO is it a bug or a feature when type date exists ?
              name: 'date',
          }, {
              relation: 'product.product',
              type: 'many2one',
              name: 'product_id',
          }], {
              account_id: {
                  string: _t("Account"),
              },
              label: { string: _t("Label") },
              amount: { string: _t("Account") },
              product_id: { string: _t("Product") }
          }).then(function (recordID) {
              self.handleCreateRecord = recordID;
              var record = self.model.get(self.handleCreateRecord);

              self.fields.account_id = new relational_fields.FieldMany2One(self,
                  'account_id', record, { mode: 'edit' });

              self.fields.journal_id = new relational_fields.FieldMany2One(self,
                  'journal_id', record, { mode: 'edit' });

              self.fields.tax_id = new relational_fields.FieldMany2One(self,
                  'tax_id', record, { mode: 'edit', additionalContext: { append_type_to_tax_name: true } });

              self.fields.analytic_account_id = new relational_fields.FieldMany2One(self,
                  'analytic_account_id', record, { mode: 'edit' });

              self.fields.analytic_tag_ids = new relational_fields.FieldMany2ManyTags(self,
                  'analytic_tag_ids', record, { mode: 'edit' });

              self.fields.force_tax_included = new basic_fields.FieldBoolean(self,
                  'force_tax_included', record, { mode: 'edit' });

              self.fields.label = new basic_fields.FieldChar(self,
                  'label', record, { mode: 'edit' });

              self.fields.amount = new basic_fields.FieldFloat(self,
                  'amount', record, { mode: 'edit' });

              self.fields.date = new basic_fields.FieldDate(self,
                  'date', record, { mode: 'edit' });

              self.fields.product_id = new relational_fields.FieldMany2One(self,
                  'product_id', record, { mode: 'edit' });

              var $create = $(qweb.render("reconciliation.line.create", { 'state': state, 'group_tags': self.group_tags, 'group_acc': self.group_acc }));
              self.fields.account_id.appendTo($create.find('.create_account_id .o_td_field'))
                  .then(addRequiredStyle.bind(self, self.fields.account_id));
              self.fields.journal_id.appendTo($create.find('.create_journal_id .o_td_field'));
              self.fields.tax_id.appendTo($create.find('.create_tax_id .o_td_field'));
              self.fields.analytic_account_id.appendTo($create.find('.create_analytic_account_id .o_td_field'));
              self.fields.analytic_tag_ids.appendTo($create.find('.create_analytic_tag_ids .o_td_field'));
              self.fields.force_tax_included.appendTo($create.find('.create_force_tax_included .o_td_field'))
              self.fields.label.appendTo($create.find('.create_label .o_td_field'))
                  .then(addRequiredStyle.bind(self, self.fields.label));
              self.fields.amount.appendTo($create.find('.create_amount .o_td_field'))
                  .then(addRequiredStyle.bind(self, self.fields.amount));
              self.fields.date.appendTo($create.find('.create_date .o_td_field'));
              self.fields.product_id.appendTo($create.find('.create_product_id .o_td_field'));
              self.$('.create').append($create);

              function addRequiredStyle(widget) {
                  widget.$el.addClass('o_required_modifier');
              }
          });
      },
    });

    reconciliation_model.ManualModel.include({
        quickCreateFields: ['product_id', 'account_id', 'amount', 'amount_type', 'analytic_account_id', 'journal_id', 'label', 'force_tax_included', 'tax_id', 'analytic_tag_ids'],

        updateProposition: function (handle, values) {
            // Update other fields when product_id is changed
            var self = this;
            if ('product_id' in values) {
                var parent = this._super;
                return this._rpc({
                    model: 'account.reconcile.model',
                    method: 'product_changed',
                    args:[{product_id: values.product_id.id}]
                }).then(function(changes) {
                    if (changes) {
                        if (changes.account_id)
                            values.account_id = changes.account_id;
                        if (changes.tax_id)
                            values.tax_id = changes.tax_id;
                    }
                    return parent.call(self, handle, values)
                });
            } else {
                return this._super(handle, values);
            }
        },

        quickCreateProposition: function (handle, reconcileModelId) {
            // Add product field from the reconcile model into the proposition
            this._super(handle, reconcileModelId);
            var line = this.getLine(handle);
            var reconcileModel = _.find(this.reconcileModels, function (r) {return r.id === reconcileModelId;});
            line.reconciliation_proposition[0].product_id = this._formatNameGet(reconcileModel.product_id);
            if (reconcileModel.has_second_line) {
                line.reconciliation_proposition[1].product_id = line.reconciliation_proposition[0].product_id;
            }
            return this._computeLine(line);
        }
    });

    return {
        renderer: reconciliation_renderer,
        model: reconciliation_model
    }
});
