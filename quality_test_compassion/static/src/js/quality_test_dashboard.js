/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, onWillStart, onWillUnmount, useState } from "@odoo/owl";

const DASHBOARD_CHANNEL = "quality_test_dashboard";
const DASHBOARD_NOTIFICATION = "quality_test_dashboard_updated";

class QualityTestDashboard extends Component {
    static template = "quality_test_compassion.QualityTestDashboard";

    setup() {
        this.actionService = useService("action");
        this.busService = useService("bus_service");
        this.orm = useService("orm");
        this.state = useState({
            cards: [],
            loading: true,
            total: 0,
        });
        this.onDashboardUpdate = () => {
            this.loadMetrics();
        };

        onWillStart(async () => {
            await this.busService.addChannel(DASHBOARD_CHANNEL);
            this.busService.subscribe(
                DASHBOARD_NOTIFICATION,
                this.onDashboardUpdate
            );
            await this.loadMetrics();
        });

        onWillUnmount(() => {
            this.busService.unsubscribe(
                DASHBOARD_NOTIFICATION,
                this.onDashboardUpdate
            );
            this.busService.deleteChannel(DASHBOARD_CHANNEL);
        });
    }

    async loadMetrics() {
        this.state.loading = true;
        const metrics = await this.orm.call(
            "quality.test",
            "get_dashboard_metrics",
            []
        );
        this.state.cards = metrics.cards;
        this.state.total = metrics.total;
        this.state.loading = false;
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

    get subtitle() {
        return _t("Live progress based on active and draft quality tests.");
    }
}

registry.category("actions").add("quality_test_dashboard", QualityTestDashboard);
