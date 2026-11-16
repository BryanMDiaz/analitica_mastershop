# -*- coding: utf-8 -*-
from odoo import models, fields, api

class PosOrder(models.Model):
    _inherit = 'pos.order'

    vendedor_id = fields.Many2one(
        'hr.employee',
        string="Vendedor Comisionista",
        index=True,
        tracking=True,
        help="Empleado/vendedor asignado a esta venta para comisiones."
    )

    def _process_order(self, order, existing_order):
        res = super()._process_order(order, existing_order)
        order_rec = self.browse(res)
        if order.get('vendedor_id') and not order_rec.vendedor_id:
            order_rec.write({'vendedor_id': order['vendedor_id']})
        return res

    def _prepare_invoice_vals(self):
        vals = super()._prepare_invoice_vals()
        if self.vendedor_id:
            vals['vendedor_id'] = self.vendedor_id.id
            if self.vendedor_id.user_id:
                vals['invoice_user_id'] = self.vendedor_id.user_id.id
        return vals

    def _apply_invoice_payments(self, is_reverse=False):
        # Garantizar automáticamente que la compañía tenga cuenta por cobrar POS para evitar errores contables
        company = self.company_id
        if not company.account_default_pos_receivable_account_id:
            receivable_acc = self.env['account.account'].search([
                ('account_type', '=', 'asset_receivable'),
                ('reconcile', '=', True),
                ('company_ids', 'in', [company.id])
            ], limit=1)
            if receivable_acc:
                company.sudo().account_default_pos_receivable_account_id = receivable_acc
        return super()._apply_invoice_payments(is_reverse)


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    is_vendedor_mastershop = fields.Boolean(
        string="Vendedor MasterShop",
        compute="_compute_is_vendedor_mastershop",
        store=True,
        readonly=False,
        index=True,
        help="Indica si el empleado o su contacto asociado tiene la etiqueta 'Vendedor Mastershop'."
    )

    @api.depends('work_contact_id.category_id', 'user_id.partner_id.category_id', 'category_ids')
    def _compute_is_vendedor_mastershop(self):
        for emp in self:
            tags = []
            if emp.work_contact_id:
                tags.extend(emp.work_contact_id.category_id.mapped('name'))
            if emp.user_id and emp.user_id.partner_id:
                tags.extend(emp.user_id.partner_id.category_id.mapped('name'))
            if emp.category_ids:
                tags.extend(emp.category_ids.mapped('name'))
            emp.is_vendedor_mastershop = any(
                'vendedor' in (t or '').lower() and 'master' in (t or '').lower()
                for t in tags
            )

    @api.model
    def _load_pos_data_fields(self, config_id):
        fields_list = super()._load_pos_data_fields(config_id)
        if 'is_vendedor_mastershop' not in fields_list:
            fields_list.append('is_vendedor_mastershop')
        return fields_list


class PosSession(models.Model):
    _inherit = 'pos.session'

    @api.model
    def _load_pos_data_models(self, config_id):
        data = super()._load_pos_data_models(config_id)
        if 'hr.employee' not in data:
            data.append('hr.employee')
        return data
