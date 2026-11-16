import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
import { patch } from "@web/core/utils/patch";
import { SelectionPopup } from "@point_of_sale/app/utils/input_popups/selection_popup";
import { makeAwaitable } from "@point_of_sale/app/store/make_awaitable_dialog";
import { _t } from "@web/core/l10n/translation";

patch(ControlButtons.prototype, {
    get currentVendedor() {
        const order = this.pos.get_order();
        if (!order || !order.vendedor_id) {
            return false;
        }
        if (typeof order.vendedor_id === "object") {
            return order.vendedor_id;
        }
        const empModel = this.pos.models && this.pos.models["hr.employee"];
        if (empModel && empModel.get) {
            return empModel.get(order.vendedor_id) || false;
        }
        return false;
    },

    async clickSelectVendedor() {
        const currentOrder = this.pos.get_order();
        if (!currentOrder) {
            return;
        }

        const empModel = this.pos.models && this.pos.models["hr.employee"];
        const employees = empModel ? (empModel.getAll ? empModel.getAll() : (empModel.orderedRecords || [])) : [];
        const currentVendedorId = currentOrder.vendedor_id?.id || currentOrder.vendedor_id || false;

        // Filtrar únicamente los empleados asignados con la etiqueta 'Vendedor Mastershop'
        const filteredEmployees = employees.filter(
            (emp) => Boolean(emp.is_vendedor_mastershop ?? emp.raw?.is_vendedor_mastershop) || emp.id === currentVendedorId
        );

        const list = [
            {
                id: 0,
                label: _t("❌ Sin Vendedor / Ninguno"),
                isSelected: !currentVendedorId,
                item: false,
            },
            ...filteredEmployees.map((emp) => ({
                id: emp.id,
                label: emp.name,
                isSelected: currentVendedorId === emp.id,
                item: emp,
            })),
        ];

        const selectedEmployee = await makeAwaitable(this.dialog, SelectionPopup, {
            title: _t("Asignar Vendedor (Comisión)"),
            list: list,
        });

        if (selectedEmployee !== undefined) {
            currentOrder.update({ vendedor_id: selectedEmployee ? selectedEmployee : false });
        }
    },
});
