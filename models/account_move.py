# -*- coding: utf-8 -*-

from odoo import models, fields, api

TARGET_PRODUCT_TERMS = ('MASTERSHOP', 'HERRAMIENTAS MASTER SHOP', 'MASTER')


class AccountMove(models.Model):
    _inherit = 'account.move'

    es_mastershop = fields.Boolean(
        string='Es Venta MasterShop',
        compute='_compute_es_mastershop',
        search='_search_es_mastershop',
        store=True,
        index=True,
        help='Indica si la factura pertenece a GRUPO 2 S.A. DE C.V., el cliente tiene la etiqueta Mastershop y contiene productos MasterShop.'
    )

    vendedor_id = fields.Many2one(
        'hr.employee',
        string="Vendedor Comisionista",
        index=True,
        tracking=True,
        help="Empleado/vendedor asignado a esta factura para cálculo de comisiones."
    )

    def _reverse_moves(self, default_values_list=None, cancel=False):
        """Hereda el vendedor_id automáticamente al crear una Nota de Crédito (devolución)."""
        if default_values_list is None:
            default_values_list = [{} for _ in self]
        for move, default_values in zip(self, default_values_list):
            if move.vendedor_id and not default_values.get('vendedor_id'):
                default_values['vendedor_id'] = move.vendedor_id.id
        return super()._reverse_moves(default_values_list, cancel)

    @api.depends('company_id', 'company_id.name', 'partner_id', 'commercial_partner_id', 'invoice_line_ids', 'invoice_line_ids.product_id', 'invoice_line_ids.name')
    def _compute_es_mastershop(self):
        for move in self:
            # 1. Sucursal exclusiva: GRUPO 2 S.A. DE C.V. (no Sucursal Terrazas)
            comp_name = (move.company_id.name or '').upper()
            if 'GRUPO 2' not in comp_name:
                move.es_mastershop = False
                continue

            # 2. El cliente DEBE tener la etiqueta Mastershop obligatoriamente
            partner = move.commercial_partner_id or move.partner_id
            is_mastershop_client = bool(
                partner.es_cliente_mastershop or
                any('mastershop' in (cat.name or '').lower() for cat in partner.category_id)
            )
            if not is_mastershop_client:
                move.es_mastershop = False
                continue

            # 3. La factura debe contener productos MasterShop / Herramientas Master Shop / MASTER
            has_target = False
            for line in move.invoice_line_ids:
                if line.display_type != 'product':
                    continue
                p_name = (line.product_id.name or '').upper() if line.product_id else ''
                p_code = (line.product_id.default_code or '').upper() if line.product_id else ''
                l_name = (line.name or '').upper()

                if any(term in p_name or term in p_code or term in l_name for term in TARGET_PRODUCT_TERMS):
                    has_target = True
                    break

            move.es_mastershop = has_target

    def _search_es_mastershop(self, operator, value):
        tag_ids = self.env['res.partner.category'].search([('name', 'ilike', 'mastershop')]).ids
        if not tag_ids:
            return [('id', '=', 0)]

        self.env.cr.execute("""
            SELECT DISTINCT m.id
            FROM account_move m
            JOIN res_company c ON c.id = m.company_id
            JOIN res_partner p ON p.id = m.commercial_partner_id
            JOIN res_partner_res_partner_category_rel rel ON rel.partner_id = p.id
            JOIN account_move_line l ON l.move_id = m.id
            LEFT JOIN product_product pp ON pp.id = l.product_id
            LEFT JOIN product_template pt ON pt.id = pp.product_tmpl_id
            WHERE c.name ILIKE '%GRUPO 2%'
              AND rel.category_id IN %s
              AND (
                  pt.name::text ILIKE '%MASTERSHOP%'
                  OR pt.name::text ILIKE '%Herramientas Master Shop%'
                  OR pt.name::text ILIKE '%MASTER%'
                  OR l.name ILIKE '%MASTERSHOP%'
                  OR l.name ILIKE '%Herramientas Master Shop%'
                  OR l.name ILIKE '%MASTER%'
              )
        """, [tuple(tag_ids)])
        matching_ids = [r[0] for r in self.env.cr.fetchall()]
        if (operator == '=' and value) or (operator == '!=' and not value):
            return [('id', 'in', matching_ids)]
        else:
            return [('id', 'not in', matching_ids)]
