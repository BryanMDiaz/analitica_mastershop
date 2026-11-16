# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class AnaliticaMastershop(models.Model):
    _name = 'analitica.mastershop'
    _description = 'Analítica y Rentabilidad MasterShop'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'fecha_inicio desc, id desc'

    name = fields.Char(
        string='Referencia / Código',
        required=True,
        copy=False,
        default=lambda self: _('Nuevo'),
        tracking=True,
    )
    tienda_nombre = fields.Char(
        string='Nombre de Tienda / Sucursal MasterShop',
        required=True,
        tracking=True,
    )
    analytic_account_id = fields.Many2one(
        'account.analytic.account',
        string='Cuenta Analítica',
        tracking=True,
        help='Cuenta analítica de Odoo asociada para registrar ingresos y costos.'
    )
    analytic_line_count = fields.Integer(
        string='Apuntes Analíticos',
        compute='_compute_analytic_line_count',
    )
    company_id = fields.Many2one(
        'res.company',
        string='Compañía',
        required=True,
        default=lambda self: self.env.company,
    )
    currency_id = fields.Many2one(
        'res.currency',
        related='company_id.currency_id',
        string='Moneda',
        readonly=True,
    )
    responsable_id = fields.Many2one(
        'res.users',
        string='Responsable',
        default=lambda self: self.env.user,
        tracking=True,
    )
    fecha_inicio = fields.Date(
        string='Fecha Inicio',
        default=fields.Date.context_today,
        tracking=True,
    )
    fecha_fin = fields.Date(
        string='Fecha Fin',
        tracking=True,
    )
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('in_progress', 'En Operación'),
        ('done', 'Finalizado'),
        ('cancel', 'Cancelado'),
    ], string='Estado', default='draft', required=True, tracking=True)

    ventas_totales = fields.Monetary(
        string='Ventas Totales',
        currency_field='currency_id',
        tracking=True,
    )
    costos_totales = fields.Monetary(
        string='Costos Operativos',
        currency_field='currency_id',
        tracking=True,
    )
    margen_bruto = fields.Monetary(
        string='Margen Bruto',
        currency_field='currency_id',
        compute='_compute_margenes',
        store=True,
    )
    porcentaje_margen = fields.Float(
        string='% Rentabilidad',
        compute='_compute_margenes',
        store=True,
        help='Porcentaje de rentabilidad sobre las ventas totales.'
    )
    notas = fields.Html(
        string='Observaciones y Estrategia',
    )

    @api.depends('ventas_totales', 'costos_totales')
    def _compute_margenes(self):
        for rec in self:
            rec.margen_bruto = (rec.ventas_totales or 0.0) - (rec.costos_totales or 0.0)
            if rec.ventas_totales:
                rec.porcentaje_margen = rec.margen_bruto / rec.ventas_totales
            else:
                rec.porcentaje_margen = 0.0

    def _compute_analytic_line_count(self):
        for rec in self:
            if rec.analytic_account_id:
                rec.analytic_line_count = self.env['account.analytic.line'].search_count([
                    ('account_id', '=', rec.analytic_account_id.id)
                ])
            else:
                rec.analytic_line_count = 0

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals.get('name') == _('Nuevo'):
                seq = self.env['ir.sequence'].next_by_code('analitica.mastershop')
                vals['name'] = seq or ('MS-' + fields.Date.today().strftime('%Y%m%d') + '-' + str(self.env['analitica.mastershop'].search_count([]) + 1).zfill(4))
        return super().create(vals_list)

    def action_set_in_progress(self):
        self.write({'state': 'in_progress'})

    def action_set_done(self):
        self.write({'state': 'done'})

    def action_set_draft(self):
        self.write({'state': 'draft'})

    def action_set_cancel(self):
        self.write({'state': 'cancel'})

    def action_view_analytic_lines(self):
        self.ensure_one()
        if not self.analytic_account_id:
            return {'type': 'ir.actions.act_window_close'}
        return {
            'name': _('Apuntes Analíticos: %s', self.analytic_account_id.display_name),
            'type': 'ir.actions.act_window',
            'res_model': 'account.analytic.line',
            'view_mode': 'list,form,pivot,graph',
            'domain': [('account_id', '=', self.analytic_account_id.id)],
            'context': {
                'default_account_id': self.analytic_account_id.id,
            },
        }
