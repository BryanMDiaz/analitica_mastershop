from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    mastershop_descontar_iva = fields.Boolean(string='Descontar IVA en comisiones')
    mastershop_descontar_renta = fields.Boolean(string='Descontar renta en comisiones')


