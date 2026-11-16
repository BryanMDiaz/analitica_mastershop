# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import timedelta


class ResPartner(models.Model):
    _inherit = 'res.partner'

    mastershop_currency_id = fields.Many2one(
        'res.currency',
        string="Moneda (MasterShop)",
        compute='_compute_mastershop_currency_id'
    )

    @api.depends('company_id')
    def _compute_mastershop_currency_id(self):
        default_currency = self.env.company.currency_id
        for partner in self:
            partner.mastershop_currency_id = partner.company_id.currency_id if partner.company_id else default_currency

    es_cliente_mastershop = fields.Boolean(
        string="Es Cliente MasterShop",
        compute="_compute_es_cliente_mastershop",
        search="_search_es_cliente_mastershop",
        store=True,
        index=True,
        help="Indica si el contacto tiene asignada la etiqueta Mastershop."
    )

    mastershop_last_sale_date = fields.Date(
        string="Fecha Últ. Venta",
        compute="_compute_mastershop_purchase_stats",
        store=True,
    )
    mastershop_last_sale_amount = fields.Monetary(
        string="Monto Últ. Venta",
        compute="_compute_mastershop_purchase_stats",
        currency_field='mastershop_currency_id',
        store=True,
    )
    mastershop_total_sales = fields.Monetary(
        string="Total Histórico",
        compute="_compute_mastershop_purchase_stats",
        currency_field='mastershop_currency_id',
        store=True,
    )
    mastershop_invoice_count = fields.Integer(
        string="Cant. Facturas",
        compute="_compute_mastershop_purchase_stats",
        store=True,
    )
    mastershop_sale_count = fields.Integer(
        string="Cant. Pedidos",
        compute="_compute_mastershop_purchase_stats",
        store=True,
    )
    mastershop_average_ticket = fields.Monetary(
        string="Gasto Promedio",
        compute="_compute_mastershop_purchase_stats",
        currency_field='mastershop_currency_id',
        store=True,
    )
    mastershop_days_since_sale = fields.Integer(
        string="Días sin Compra",
        compute="_compute_mastershop_purchase_stats",
        search="_search_mastershop_days_since_sale",
        store=True,
    )
    mastershop_avg_days_between = fields.Float(
        string="Frecuencia Habitual (Días)",
        compute="_compute_mastershop_purchase_stats",
        store=True,
    )
    mastershop_next_purchase_prob = fields.Date(
        string="Próxima Compra Estimada",
        compute="_compute_mastershop_purchase_stats",
        store=True,
    )

    @api.depends('category_id')
    def _compute_es_cliente_mastershop(self):
        for partner in self:
            is_tagged = any('mastershop' in (cat.name or '').lower() for cat in partner.category_id)
            partner.es_cliente_mastershop = bool(is_tagged)

    def _search_es_cliente_mastershop(self, operator, value):
        tag_ids = self.env['res.partner.category'].search([('name', 'ilike', 'mastershop')]).ids
        if not tag_ids:
            return [('id', '=', 0)] if (operator == '=' and value) else []
        if (operator == '=' and value) or (operator == '!=' and not value):
            return [('category_id', 'in', tag_ids)]
        else:
            return [('category_id', 'not in', tag_ids)]

    @api.depends('invoice_ids', 'invoice_ids.state', 'invoice_ids.move_type', 'invoice_ids.invoice_date', 'invoice_ids.amount_untaxed_signed')
    def _compute_mastershop_purchase_stats(self):
        partner_ids = set(self.ids)
        commercial_ids = set(self.mapped('commercial_partner_id').ids)
        all_target_ids = list(partner_ids | commercial_ids)

        if all_target_ids:
            all_invoices = self.env['account.move'].search([
                '|',
                ('commercial_partner_id', 'in', all_target_ids),
                ('partner_id', 'in', all_target_ids),
                ('move_type', 'in', ('out_invoice', 'out_refund')),
                ('state', '=', 'posted'),
            ], order='invoice_date desc, id desc')

            all_orders = self.env['sale.order'].search([
                '|',
                ('partner_id', 'in', all_target_ids),
                ('partner_id.commercial_partner_id', 'in', all_target_ids),
                ('state', 'in', ('sale', 'done')),
            ])
        else:
            all_invoices = self.env['account.move']
            all_orders = self.env['sale.order']

        invoices_by_comm_id = {}
        invoices_by_partner_id = {}
        for inv in all_invoices:
            c_id = inv.commercial_partner_id.id
            p_id = inv.partner_id.id
            if c_id:
                invoices_by_comm_id.setdefault(c_id, []).append(inv)
            if p_id:
                invoices_by_partner_id.setdefault(p_id, []).append(inv)

        orders_by_comm_id = {}
        for order in all_orders:
            c_id = order.partner_id.commercial_partner_id.id or order.partner_id.id
            orders_by_comm_id.setdefault(c_id, []).append(order)

        today = fields.Date.today()

        for partner in self:
            partner_invs = []
            seen_ids = set()
            candidate_invs = (
                invoices_by_partner_id.get(partner.id, []) +
                invoices_by_comm_id.get(partner.commercial_partner_id.id, [])
            )
            for inv in candidate_invs:
                if inv.id not in seen_ids:
                    seen_ids.add(inv.id)
                    partner_invs.append(inv)

            partner_invs.sort(key=lambda x: (x.invoice_date or fields.Date.min, x.id), reverse=True)
            sales_invoices = [inv for inv in partner_invs if inv.move_type == 'out_invoice']

            partner_orders = orders_by_comm_id.get(partner.commercial_partner_id.id, [])
            partner.mastershop_sale_count = len(partner_orders)

            if not sales_invoices:
                partner.mastershop_last_sale_date = False
                partner.mastershop_last_sale_amount = 0.0
                partner.mastershop_total_sales = 0.0
                partner.mastershop_invoice_count = 0
                partner.mastershop_average_ticket = 0.0
                partner.mastershop_days_since_sale = False
                partner.mastershop_next_purchase_prob = False
                partner.mastershop_avg_days_between = 0.0
                continue

            partner.mastershop_last_sale_date = sales_invoices[0].invoice_date
            partner.mastershop_last_sale_amount = sales_invoices[0].amount_untaxed_signed
            partner.mastershop_total_sales = sum(inv.amount_untaxed_signed for inv in partner_invs)
            partner.mastershop_invoice_count = len(sales_invoices)
            partner.mastershop_average_ticket = (
                partner.mastershop_total_sales / partner.mastershop_invoice_count
                if partner.mastershop_invoice_count else 0.0
            )

            if partner.mastershop_last_sale_date:
                delta = today - partner.mastershop_last_sale_date
                partner.mastershop_days_since_sale = delta.days
            else:
                partner.mastershop_days_since_sale = False

            days_diffs = []
            if len(sales_invoices) > 1:
                for i in range(len(sales_invoices) - 1):
                    d1 = sales_invoices[i].invoice_date
                    d2 = sales_invoices[i + 1].invoice_date
                    if d1 and d2:
                        days_diffs.append(abs((d1 - d2).days))

            avg_days = sum(days_diffs) / len(days_diffs) if days_diffs else 0.0
            partner.mastershop_avg_days_between = avg_days
            if avg_days > 0 and partner.mastershop_last_sale_date:
                partner.mastershop_next_purchase_prob = partner.mastershop_last_sale_date + timedelta(days=int(avg_days))
            else:
                partner.mastershop_next_purchase_prob = False

    def _search_mastershop_days_since_sale(self, operator, value):
        target_date = fields.Date.today() - timedelta(days=value)
        tag_ids = self.env['res.partner.category'].search([('name', 'ilike', 'mastershop')]).ids
        if not tag_ids:
            return [('id', '=', 0)]

        # Get commercial_partner_ids with Mastershop tag
        self.env.cr.execute("""
            SELECT DISTINCT m.commercial_partner_id, MAX(m.invoice_date) as last_date
            FROM account_move m
            JOIN res_partner p ON p.id = m.commercial_partner_id
            JOIN res_partner_res_partner_category_rel rel ON rel.partner_id = p.id
            WHERE m.move_type = 'out_invoice' AND m.state = 'posted'
              AND rel.category_id IN %s
            GROUP BY m.commercial_partner_id
        """, [tuple(tag_ids)])
        results = self.env.cr.dictfetchall()

        matched_partner_ids = []
        for row in results:
            last_date = row['last_date']
            if not last_date:
                continue

            if operator == '<=' and last_date >= target_date:
                matched_partner_ids.append(row['commercial_partner_id'])
            elif operator == '>' and last_date < target_date:
                matched_partner_ids.append(row['commercial_partner_id'])
            elif operator == '<' and last_date > target_date:
                matched_partner_ids.append(row['commercial_partner_id'])
            elif operator == '>=' and last_date <= target_date:
                matched_partner_ids.append(row['commercial_partner_id'])
            elif operator == '=' and last_date == target_date:
                matched_partner_ids.append(row['commercial_partner_id'])

        if operator in ('>', '>=') and value >= 90:
            # Include tagged partners that never purchased
            self.env.cr.execute("""
                SELECT p.id FROM res_partner p
                JOIN res_partner_res_partner_category_rel rel ON rel.partner_id = p.id
                WHERE rel.category_id IN %s
                  AND p.id NOT IN (
                      SELECT DISTINCT commercial_partner_id FROM account_move
                      WHERE move_type = 'out_invoice' AND state = 'posted' AND commercial_partner_id IS NOT NULL
                  )
            """, [tuple(tag_ids)])
            matched_partner_ids.extend([r[0] for r in self.env.cr.fetchall()])

        return [('id', 'in', matched_partner_ids)]

    def action_view_mastershop_invoices(self):
        self.ensure_one()
        return {
            'name': f'Facturas de {self.name} (MasterShop)',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [
                '|',
                ('partner_id', 'child_of', self.commercial_partner_id.id),
                ('commercial_partner_id', '=', self.commercial_partner_id.id),
                ('move_type', 'in', ('out_invoice', 'out_refund')),
                ('state', '=', 'posted'),
            ],
            'context': {
                'default_partner_id': self.id,
                'default_move_type': 'out_invoice',
            },
        }

    def action_view_mastershop_sale_orders(self):
        self.ensure_one()
        return {
            'name': f'Pedidos de Venta: {self.name} (MasterShop)',
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'view_mode': 'list,form',
            'domain': [
                '|',
                ('partner_id', 'child_of', self.commercial_partner_id.id),
                ('partner_id', '=', self.id),
            ],
            'context': {
                'default_partner_id': self.id,
            },
        }
