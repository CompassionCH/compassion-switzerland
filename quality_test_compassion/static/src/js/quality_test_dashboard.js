/* eslint-disable jsdoc/check-tag-names */
/** @odoo-module **/

import { Component, onWillStart, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

class QualityTestDashboard extends Component {
  static template = "quality_test_compassion.QualityTestDashboard";

  setup() {
    this.actionService = useService("action");
    this.orm = useService("orm");
    this.state = useState({
      cards: [],
      loading: true,
      subtitle: "",
      title: "",
      total: 0,
    });

    onWillStart(async () => {
      await this.loadMetrics();
    });
  }

  async loadMetrics() {
    this.state.loading = true;
    const metrics = await this.orm.call(
      "quality.test",
      "get_dashboard_metrics",
      [],
    );
    this.state.cards = metrics.cards;
    this.state.subtitle = metrics.subtitle;
    this.state.title = metrics.title;
    this.state.total = metrics.total;
    this.state.loading = false;
  }

  formatPercentage(value) {
    return `${value.toFixed(1)}%`;
  }

  openCard(card) {
    this.actionService.doAction({
      context: {},
      domain: card.domain || [],
      name: card.action_name || card.title,
      res_model: "quality.test",
      target: "current",
      type: "ir.actions.act_window",
      view_mode: "list,form",
      views: [
        [false, "list"],
        [false, "form"],
      ],
    });
  }
}

registry
  .category("actions")
  .add("quality_test_dashboard", QualityTestDashboard);
