import { PosOrder } from "@point_of_sale/app/models/pos_order";
import { patch } from "@web/core/utils/patch";

patch(PosOrder.prototype, {
    setup(vals) {
        super.setup(...arguments);
        this.vendedor_id = (vals && vals.vendedor_id) || false;
    },
    serialize(options = {}) {
        const data = super.serialize(...arguments);
        data.vendedor_id = this.vendedor_id ? (this.vendedor_id.id || this.vendedor_id) : false;
        return data;
    },
    export_for_printing(baseUrl, headerData) {
        const result = super.export_for_printing(...arguments);
        if (result && result.headerData) {
            let vendedorName = false;
            if (this.vendedor_id) {
                let fullName = false;
                if (typeof this.vendedor_id === 'object' && this.vendedor_id.name) {
                    fullName = this.vendedor_id.name;
                } else if (typeof this.vendedor_id === 'number' || typeof this.vendedor_id === 'string') {
                    const empId = parseInt(this.vendedor_id);
                    const emp = this.models && this.models['hr.employee'] && this.models['hr.employee'].get(empId);
                    fullName = (emp && emp.name) ? emp.name : false;
                }
                if (fullName) {
                    const parts = fullName.trim().split(/\s+/);
                    vendedorName = parts.length >= 2 ? parts[0] + ' ' + parts[parts.length >= 4 ? 2 : 1] : parts[0];
                }
            }
            result.headerData.vendedor = vendedorName;
        }
        return result;
    },
});
