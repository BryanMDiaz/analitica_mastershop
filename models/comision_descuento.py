# -*- coding: utf-8 -*-
from odoo import models, fields


class MastershopComisionDescuento(models.Model):
    _name = 'mastershop.comision.descuento'
    _description = 'Descuentos de Comisión MasterShop'
    _order = 'fecha desc, id desc'

    vendedor_id = fields.Many2one(
        'hr.employee',
        string='Vendedor Comisionista',
        required=True,
        ondelete='cascade',
        index=True
    )
    fecha = fields.Date(
        string='Fecha',
        default=fields.Date.context_today,
        required=True
    )
    motivo = fields.Char(
        string='Motivo / Concepto',
        required=True,
        placeholder='Ej. Envío devuelto, flete cliente no recibido, etc.'
    )
    monto = fields.Float(
        string='Monto a Descontar ($)',
        required=True,
        digits=(16, 2)
    )
    company_id = fields.Many2one(
        'res.company',
        string='Compañía',
        default=lambda self: self.env.company
    )


    def action_eliminar_descuento(self):
        """Elimina el descuento y vuelve al reporte para recalcular el saldo."""
        self.ensure_one()
        self.unlink()
        return {'type': 'ir.actions.act_window_close'}
