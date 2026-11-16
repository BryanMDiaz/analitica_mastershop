/** @odoo-module **/

import { Component, onWillStart, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

export class MastershopDashboard extends Component {
    static template = "analitica_mastershop.MastershopDashboard";

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({
            loading: true,
            selectedYear: null,
            selectedMonth: null,
            data: {
                selected_period: "",
                available_months: [],
                historico_mensual: [],
                mes_actual: {
                    nombre: "Mes Actual",
                    subtotal: 0.0,
                    subtotal_fmt: "$0.00",
                    total: 0.0,
                    total_fmt: "$0.00",
                    facturas: 0,
                    pos_ventas_fmt: "$0.00",
                    conta_ventas_fmt: "$0.00",
                    pct_pos: 50,
                    pct_conta: 50,
                },
                mes_anterior: {
                    nombre: "Mes Anterior",
                    subtotal: 0.0,
                    subtotal_fmt: "$0.00",
                    total_fmt: "$0.00",
                    facturas: 0,
                },
                variacion: {
                    pct: 0.0,
                    positiva: true,
                },
                total_anual: {
                    anio: new Date().getFullYear(),
                    monto: 0.0,
                    monto_fmt: "$0.00",
                    subtotal_fmt: "$0.00",
                },
                comisiones: {
                    ventas_comision_fmt: "$0.00",
                    descuentos_fmt: "$0.00",
                    neto_fmt: "$0.00",
                },
                clientes_salud: {
                    total: 0,
                    activos: 0,
                    alerta: 0,
                    riesgo: 0,
                },
                top_clientes: [],
                top_vendedores: [],
                top_productos: [],
            },
        });

        onWillStart(async () => {
            await this.loadData();
        });
    }

    async loadData(year = null, month = null) {
        this.state.loading = true;
        try {
            const args = [];
            if (typeof year === "number" && typeof month === "number") {
                args.push(year, month);
                this.state.selectedYear = year;
                this.state.selectedMonth = month;
            } else if (this.state.selectedYear && this.state.selectedMonth) {
                args.push(this.state.selectedYear, this.state.selectedMonth);
            }
            const result = await this.orm.call("analitica.mastershop", "get_dashboard_kpis", args);
            if (result && result.mes_actual) {
                this.state.data = result;
                if (!this.state.selectedYear && result.selected_year) {
                    this.state.selectedYear = result.selected_year;
                    this.state.selectedMonth = result.selected_month;
                }
            }
        } catch (e) {
            console.error("Error cargando KPIs de MasterShop:", e);
        } finally {
            this.state.loading = false;
        }
    }

    onPeriodChange(ev) {
        const val = ev.target.value;
        if (!val) return;
        const [y, m] = val.split("-");
        this.loadData(parseInt(y), parseInt(m));
    }

    selectPeriod(year, month) {
        if (!year || !month) return;
        this.loadData(parseInt(year), parseInt(month));
    }

    openInvoicesMonth() {
        const year = this.state.selectedYear || new Date().getFullYear();
        const month = this.state.selectedMonth || (new Date().getMonth() + 1);
        const mStr = String(month).padStart(2, "0");
        const lastDay = new Date(year, month, 0).getDate();
        const start = `${year}-${mStr}-01`;
        const end = `${year}-${mStr}-${String(lastDay).padStart(2, "0")}`;

        this.action.doAction({
            name: `Facturas MasterShop - ${this.state.data.selected_period || ""}`,
            type: "ir.actions.act_window",
            res_model: "account.move",
            views: [[false, "list"], [false, "form"]],
            view_mode: "list,form",
            domain: [
                ["move_type", "in", ["out_invoice", "out_refund"]],
                ["state", "=", "posted"],
                "|", "|",
                ["es_mastershop", "=", true],
                ["pos_order_ids", "!=", false],
                ["vendedor_id", "!=", false],
                ["invoice_date", ">=", start],
                ["invoice_date", "<=", end],
            ],
            context: {
                search_default_filter_invoices: 1,
            },
        });
    }

    openInvoicesYear() {
        const year = this.state.selectedYear || new Date().getFullYear();
        const start = `${year}-01-01`;
        const end = `${year}-12-31`;

        this.action.doAction({
            name: `Facturas MasterShop - Año ${year}`,
            type: "ir.actions.act_window",
            res_model: "account.move",
            views: [[false, "list"], [false, "form"]],
            view_mode: "list,form",
            domain: [
                ["move_type", "in", ["out_invoice", "out_refund"]],
                ["state", "=", "posted"],
                "|", "|",
                ["es_mastershop", "=", true],
                ["pos_order_ids", "!=", false],
                ["vendedor_id", "!=", false],
                ["invoice_date", ">=", start],
                ["invoice_date", "<=", end],
            ],
            context: {
                search_default_filter_invoices: 1,
            },
        });
    }

    openClientesMastershop() {
        this.action.doAction("analitica_mastershop.action_analitica_mastershop_clientes");
    }

    openComisiones() {
        this.action.doAction("analitica_mastershop.action_mastershop_comisiones");
    }

    openPartner(partnerId, partnerName) {
        if (!partnerId) return;
        this.action.doAction({
            name: partnerName || "Cliente MasterShop",
            type: "ir.actions.act_window",
            res_model: "res.partner",
            res_id: partnerId,
            views: [[false, "form"]],
            view_mode: "form",
        });
    }
}

registry.category("actions").add("mastershop_dashboard", MastershopDashboard);
