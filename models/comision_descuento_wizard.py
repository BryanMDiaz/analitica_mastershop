# -*- coding: utf-8 -*-
from odoo import models, fields, api


class MastershopComisionDescuentoWizard(models.TransientModel):
    _name = 'mastershop.comision.descuento.wizard'
    _description = 'Registrar Descuento de Comisión'

    vendedor_id = fields.Many2one(
        'hr.employee',
        string='Vendedor Comisionista',
        required=True,
        readonly=True
    )
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    fecha = fields.Date(
        string='Fecha',
        default=fields.Date.context_today,
        required=True
    )
    motivo = fields.Char(
        string='Motivo / Concepto',
        required=True
    )
    monto = fields.Float(
        string='Monto a Descontar ($)',
        required=True,
        digits=(16, 2)
    )

    def action_aplicar_descuento(self):
        self.ensure_one()
        self.env['mastershop.comision.descuento'].create({
            'vendedor_id': self.vendedor_id.id,
            'company_id': self.company_id.id,
            'fecha': self.fecha,
            'motivo': self.motivo,
            'monto': self.monto,
        })
        return {'type': 'ir.actions.act_window_close'}

