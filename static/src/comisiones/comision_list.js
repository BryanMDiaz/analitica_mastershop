/** @odoo-module **/

import { onWillStart, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { ListController } from "@web/views/list/list_controller";
import { listView } from "@web/views/list/list_view";

export class MastershopComisionController extends ListController {
    static template = "analitica_mastershop.ComisionListView";

    setup() {
        super.setup();
        this.comisionOrm = useService("orm");
        this.comisionAction = useService("action");
        this.deducciones = useState({ loading: true, busy: false });
        onWillStart(async () => {
            Object.assign(this.deducciones, await this.comisionOrm.call(
                "mastershop.comision.reporte", "get_deducciones", []
            ));
            this.deducciones.loading = false;
        });
    }

    abrirPorcentajes() {
        return this.comisionAction.doAction("analitica_mastershop.action_mastershop_comision_reglas");
    }

    async cambiarDeduccion(campo, event) {
        const valor = event.target.checked;
        // OWL keeps the persisted state until the server accepts the change.
        event.target.checked = this.deducciones[campo];
        this.deducciones.busy = true;
        try {
            Object.assign(this.deducciones, await this.comisionOrm.call(
                "mastershop.comision.reporte", "set_deduccion",
                [this.deducciones.company_id, campo, valor]
            ));
            await this.model.load();
        } finally {
            this.deducciones.busy = false;
        }
    }
}

registry.category("views").add("mastershop_comisiones", {
    ...listView,
    Controller: MastershopComisionController,
});
