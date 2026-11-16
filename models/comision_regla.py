from odoo import api, fields, models
from odoo.exceptions import ValidationError


class MastershopComisionRegla(models.Model):
    _name = 'mastershop.comision.regla'
    _description = 'Porcentajes de comisión MasterShop'
    _order = 'fecha_inicio desc, id desc'
    _check_company_auto = True

    name = fields.Char(string='Nombre de la regla', required=True)
    company_id = fields.Many2one('res.company', string='Compañía', required=True,
                                 default=lambda self: self.env.company, index=True)
    tipo = fields.Selection([('grupo', 'Un grupo de personas'), ('individual', 'Una persona'), ('temporada', 'Todos por temporada')],
                            string='Aplicar a', required=True, default='grupo')
    vendedor_id = fields.Many2one('hr.employee', string='Vendedor', check_company=True,
                                  ondelete='restrict', index=True)
    vendedor_ids = fields.Many2many(
        'hr.employee', 'mastershop_comision_regla_employee_rel', 'regla_id', 'employee_id',
        string='Personas del grupo', check_company=True,
        help='Seleccione todas las personas que compartirán este porcentaje y estas fechas.')
    cantidad_vendedores = fields.Integer(string='Personas', compute='_compute_cantidad_vendedores')

    @api.depends('tipo', 'vendedor_id', 'vendedor_ids')
    def _compute_cantidad_vendedores(self):
        for regla in self:
            regla.cantidad_vendedores = len(regla.vendedor_ids) if regla.tipo == 'grupo' else int(bool(regla.vendedor_id))

    porcentaje = fields.Float(string='Comisión (%)', required=True, digits=(5, 2))
    fecha_inicio = fields.Date(string='Desde', required=True, default=fields.Date.context_today)
    fecha_fin = fields.Date(string='Hasta', help='Vacío: sin fecha de finalización. Ambas fechas son inclusivas.')

    _sql_constraints = [
        ('porcentaje_valido', 'CHECK(porcentaje >= 0 AND porcentaje <= 100)',
         'El porcentaje debe estar entre 0 y 100.'),
        ('fechas_validas', 'CHECK(fecha_fin IS NULL OR fecha_fin >= fecha_inicio)',
         'La fecha final no puede ser anterior a la inicial.'),
        ('vendedor_valido', "CHECK((tipo = 'individual' AND vendedor_id IS NOT NULL) OR "
         "(tipo IN ('grupo', 'temporada') AND vendedor_id IS NULL))",
         'Indique un vendedor solo para las reglas individuales.'),
    ]

    @api.onchange('tipo')
    def _onchange_tipo(self):
        if self.tipo != 'individual':
            self.vendedor_id = False
        if self.tipo != 'grupo':
            self.vendedor_ids = False

    @api.constrains('tipo', 'vendedor_ids')
    def _check_integrantes(self):
        for regla in self:
            if regla.tipo == 'grupo' and not regla.vendedor_ids:
                raise ValidationError('Seleccione al menos una persona para el grupo.')
            if regla.tipo != 'grupo' and regla.vendedor_ids:
                raise ValidationError('Solo las reglas de grupo pueden tener varias personas.')

    @api.constrains('company_id', 'tipo', 'vendedor_id', 'vendedor_ids', 'fecha_inicio', 'fecha_fin')
    def _check_solapamiento(self):
        for regla in self:
            domain = [
                ('id', '!=', regla.id), ('company_id', '=', regla.company_id.id),
                ('tipo', '=', regla.tipo),
                '|', ('fecha_fin', '=', False), ('fecha_fin', '>=', regla.fecha_inicio),
            ]
            if regla.tipo == 'individual':
                domain.append(('vendedor_id', '=', regla.vendedor_id.id))
            elif regla.tipo == 'grupo':
                domain.append(('vendedor_ids', 'in', regla.vendedor_ids.ids))
            if regla.fecha_fin:
                domain.append(('fecha_inicio', '<=', regla.fecha_fin))
            if self.sudo().search_count(domain):
                raise ValidationError('Hay personas con otra regla del mismo tipo en esas fechas, '
                                      'o dos temporadas superpuestas. Ajuste los integrantes o las fechas. '
                                      'Puede usar una regla individual como excepción a un grupo.')
