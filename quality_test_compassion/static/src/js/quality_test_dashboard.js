/* eslint-disable jsdoc/check-tag-names */
/** @odoo-module **/

import { Component, onWillStart, useState } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

class QualityTestDashboard extends Component {
    static template = "quality_test_compassion.QualityTestDashboard";

    setup() {
        this.actionService = useService("action");
        this.orm = useService("orm");
        this.state = useState({
            cards: [],
            generatedAt: "",
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
        const metrics = await this.orm.call("quality.test", "get_dashboard_metrics", []);
        this.state.cards = metrics.cards;
        this.state.generatedAt = metrics.generated_at;
        this.state.subtitle = metrics.subtitle;
        this.state.title = metrics.title;
        this.state.total = metrics.total;
        this.state.loading = false;
    }

    formatDelta(value) {
        return `${value > 0 ? "+" : ""}${value.toFixed(1)} pts`;
    }

    formatPercentage(value) {
        return `${value.toFixed(1)}%`;
    }

    openCard(card) {
        this.actionService.doAction({
            context: card.context || {},
            domain: card.domain || [],
            name: card.action_name || card.title,
            res_model: "quality.test",
            target: "current",
            type: "ir.actions.act_window",
            view_mode: "list,form",
        });
    }

    get generatedAtLabel() {
        return this.state.generatedAt
            ? _t("Snapshot generated on %s").replace("%s", this.state.generatedAt)
            : "";
    }
}

registry.category("actions").add("quality_test_dashboard", QualityTestDashboard);
