# -*- coding: utf-8 -*-
from odoo import models, fields, tools


class MastershopComisionReporte(models.Model):
    _name = 'mastershop.comision.reporte'
    _description = 'Reporte de Comisiones MasterShop'
    _auto = False
    _rec_name = 'vendedor_id'
    _order = 'total_neto desc'

    vendedor_id = fields.Many2one(
        'hr.employee', string='Vendedor Comisionista', readonly=True
    )
    total_ventas = fields.Float(
        string='Total Ventas', readonly=True, digits=(16, 2)
    )
    total_facturas = fields.Integer(
        string='Cant. Facturas', readonly=True
    )
    total_devoluciones = fields.Float(
        string='Devoluciones', readonly=True
    )
    total_descuentos = fields.Float(
        string='Descuentos / Envíos', readonly=True, digits=(16, 2)
    )
    total_neto = fields.Float(
        string='Neto a Liquidar', readonly=True, digits=(16, 2)
    )
    currency_id = fields.Many2one(
        'res.currency', string='Moneda', readonly=True
    )

    company_id = fields.Many2one('res.company', string='Compañía', readonly=True)
    total_comision = fields.Float(string='Comisión generada', readonly=True, digits=(16, 2))
    total_iva = fields.Float(string='IVA (13%)', readonly=True, digits=(16, 2))
    total_renta = fields.Float(string='Renta (10%)', readonly=True, digits=(16, 2))
    sin_porcentaje = fields.Integer(string='Documentos sin porcentaje', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW mastershop_comision_reporte AS (
                WITH documentos AS (
                    SELECT am.*, r.porcentaje,
                           CASE WHEN am.move_type = 'out_refund' THEN -1 ELSE 1 END AS signo
                    FROM account_move am
                    LEFT JOIN account_move origen ON origen.id = am.reversed_entry_id
                    LEFT JOIN LATERAL (
                        SELECT regla.porcentaje
                        FROM mastershop_comision_regla regla
                        WHERE regla.company_id = am.company_id
                          AND (regla.tipo = 'temporada'
                               OR (regla.tipo = 'individual' AND regla.vendedor_id = am.vendedor_id)
                               OR (regla.tipo = 'grupo' AND EXISTS (
                                   SELECT 1 FROM mastershop_comision_regla_employee_rel miembros
                                   WHERE miembros.regla_id = regla.id AND miembros.employee_id = am.vendedor_id
                               )))
                          AND regla.fecha_inicio <= COALESCE(origen.invoice_date, origen.date, am.invoice_date, am.date)
                          AND (regla.fecha_fin IS NULL OR regla.fecha_fin >= COALESCE(origen.invoice_date, origen.date, am.invoice_date, am.date))
                        ORDER BY (regla.tipo = 'temporada') DESC, (regla.tipo = 'individual') DESC, regla.fecha_inicio DESC, regla.id DESC
                        LIMIT 1
                    ) r ON TRUE
                    WHERE am.vendedor_id IS NOT NULL
                      AND am.move_type IN ('out_invoice', 'out_refund') AND am.state = 'posted'
                ), ventas_base AS (
                    SELECT vendedor_id, company_id, currency_id,
                        SUM(CASE WHEN move_type = 'out_invoice' THEN amount_total ELSE 0 END) AS total_ventas,
                        SUM(CASE WHEN move_type = 'out_refund' THEN amount_total ELSE 0 END) AS total_devoluciones,
                        COUNT(*) FILTER (WHERE move_type = 'out_invoice') AS total_facturas,
                        COUNT(*) FILTER (WHERE porcentaje IS NULL) AS sin_porcentaje,
                        SUM(ROUND((signo * amount_total * COALESCE(porcentaje, 0) / 100)::numeric,
                                  (SELECT decimal_places FROM res_currency WHERE id = currency_id))) AS total_comision
                    FROM documentos
                    GROUP BY vendedor_id, company_id, currency_id
                ), deducciones AS (
                    SELECT v.*,
                        CASE WHEN c.mastershop_descontar_iva THEN
                            ROUND(GREATEST(v.total_comision, 0) * 0.13, moneda.decimal_places)
                            ELSE 0 END AS total_iva,
                        CASE WHEN c.mastershop_descontar_renta THEN
                            ROUND(GREATEST(v.total_comision, 0) * 0.10, moneda.decimal_places)
                            ELSE 0 END AS total_renta
                    FROM ventas_base v
                    JOIN res_company c ON c.id = v.company_id
                    JOIN res_currency moneda ON moneda.id = v.currency_id
                ), ventas AS (
                    SELECT vendedor_id, company_id, currency_id,
                        SUM(total_ventas) AS total_ventas,
                        SUM(total_devoluciones) AS total_devoluciones,
                        SUM(total_facturas) AS total_facturas,
                        SUM(sin_porcentaje) AS sin_porcentaje,
                        SUM(total_comision) AS total_comision,
                        SUM(total_iva) AS total_iva,
                        SUM(total_renta) AS total_renta
                    FROM deducciones
                    GROUP BY vendedor_id, company_id, currency_id
                ), descuentos AS (
                    SELECT d.vendedor_id, COALESCE(d.company_id, e.company_id) AS company_id,
                           c.currency_id, SUM(COALESCE(d.monto, 0)) AS total_descuentos
                    FROM mastershop_comision_descuento d
                    JOIN hr_employee e ON e.id = d.vendedor_id
                    JOIN res_company c ON c.id = COALESCE(d.company_id, e.company_id)
                    GROUP BY d.vendedor_id, COALESCE(d.company_id, e.company_id), c.currency_id
                ), claves AS (
                    SELECT vendedor_id, company_id, currency_id FROM ventas
                    UNION
                    SELECT vendedor_id, company_id, currency_id FROM descuentos
                )
                SELECT ROW_NUMBER() OVER (ORDER BY k.vendedor_id, k.company_id, k.currency_id)::integer AS id,
                    k.vendedor_id, k.company_id, k.currency_id,
                    COALESCE(v.total_ventas, 0) AS total_ventas,
                    COALESCE(v.total_devoluciones, 0) AS total_devoluciones,
                    COALESCE(v.total_facturas, 0) AS total_facturas,
                    COALESCE(v.sin_porcentaje, 0) AS sin_porcentaje,
                    COALESCE(v.total_comision, 0) AS total_comision,
                    COALESCE(d.total_descuentos, 0) AS total_descuentos,
                    COALESCE(v.total_iva, 0) AS total_iva,
                    COALESCE(v.total_renta, 0) AS total_renta,
                    COALESCE(v.total_comision, 0) - COALESCE(d.total_descuentos, 0)
                        - COALESCE(v.total_iva, 0) - COALESCE(v.total_renta, 0) AS total_neto
                FROM claves k
                LEFT JOIN ventas v USING (vendedor_id, company_id, currency_id)
                LEFT JOIN descuentos d USING (vendedor_id, company_id, currency_id)
            )
        """)

    def action_ver_facturas(self):
        """Abre las facturas del vendedor seleccionado."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Facturas de {self.vendedor_id.name}',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [
                ('vendedor_id', '=', self.vendedor_id.id),
                ('company_id', '=', self.company_id.id),
                ('currency_id', '=', self.currency_id.id),
                ('move_type', 'in', ('out_invoice', 'out_refund')),
                ('state', '=', 'posted'),
            ],
            'context': {'create': False},
        }

    def action_agregar_descuento_modal(self):
        """Abre modal directo para registrar un descuento/envío con campos listos para rellenar."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Registrar Descuento / Envío - {self.vendedor_id.name}',
            'res_model': 'mastershop.comision.descuento.wizard',
            'view_mode': 'form',
            'views': [(self.env.ref('analitica_mastershop.view_mastershop_comision_descuento_wizard_form').id, 'form')],
            'target': 'new',
            'context': {
                'default_vendedor_id': self.vendedor_id.id,
                'default_company_id': self.company_id.id,
            },
        }

    def action_gestionar_descuentos(self):
        """Abre el historial de descuentos de este vendedor para ver o editar en lista."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Historial de Descuentos - {self.vendedor_id.name}',
            'res_model': 'mastershop.comision.descuento',
            'view_mode': 'list',
            'views': [(self.env.ref('analitica_mastershop.view_mastershop_comision_descuento_tree').id, 'list')],
            'domain': [('vendedor_id', '=', self.vendedor_id.id), ('company_id', '=', self.company_id.id)],
            'context': {
                'create': True, 'edit': True, 'delete': True,
                'default_vendedor_id': self.vendedor_id.id,
                'default_company_id': self.company_id.id,
            },
            'target': 'new',
        }

    def action_configurar_porcentaje(self):
        self.ensure_one()
        facturas = self.env['account.move'].search([
            ('vendedor_id', '=', self.vendedor_id.id),
            ('company_id', '=', self.company_id.id),
            ('move_type', 'in', ('out_invoice', 'out_refund')),
            ('state', '=', 'posted'),
        ], order='date asc, id asc', limit=1)
        return {
            'type': 'ir.actions.act_window', 'name': 'Asignar porcentaje',
            'res_model': 'mastershop.comision.regla', 'view_mode': 'form',
            'context': {
                'create': True, 'default_tipo': 'individual',
                'default_vendedor_id': self.vendedor_id.id,
                'default_company_id': self.company_id.id,
                'default_name': 'Comisión de %s' % self.vendedor_id.name,
                'default_fecha_inicio': (facturas.invoice_date or facturas.date) if facturas else fields.Date.context_today(self),
            },
        }
