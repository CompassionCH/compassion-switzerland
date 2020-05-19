/* This is Javascript extension of module account
   in order to add custom reconcile buttons in the
   Manual Reconcile view */

// TODO CO-3190 Migrate this JS !
odoo.define('account_reconcile_compassion.reconciliation', function (require) {
    'use strict';

    var reconciliation = require('account_reconcile_create_invoice.reconciliation');

    // Extend the class written in module account (bank statement view)
    reconciliation.bankStatementReconciliationLine.include({
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
});
