odoo.define("account_switzerland.switzerland_search_utils", function (require) {
  "use strict";

  var searchUtils = require("web.searchUtils");

  // Remove quarter options
  delete searchUtils.PERIOD_OPTIONS.fourth_quarter;
  delete searchUtils.PERIOD_OPTIONS.third_quarter;
  delete searchUtils.PERIOD_OPTIONS.second_quarter;
  delete searchUtils.PERIOD_OPTIONS.first_quarter;
  delete searchUtils.INTERVAL_OPTIONS.quarter;
});
