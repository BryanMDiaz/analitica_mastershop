from odoo import api, models
from odoo.exceptions import AccessError, ValidationError


class MastershopComisionDeducciones(models.Model):
    _inherit = 'mastershop.comision.reporte'

    @api.model
    def get_deducciones(self):
        self.check_access_rights('read')
        company = self.env.company
        return {
            'company_id': company.id,
            'company_name': company.name,
            'iva': company.mastershop_descontar_iva,
            'renta': company.mastershop_descontar_renta,
            'can_edit': self.env.user.has_group('analitica_mastershop.group_analitica_mastershop_manager'),
        }

    @api.model
    def set_deduccion(self, company_id, campo, valor):
        self.check_access_rights('read')
        if not self.env.user.has_group('analitica_mastershop.group_analitica_mastershop_manager'):
            raise AccessError('Solo los administradores de Analítica MasterShop pueden cambiar los descuentos generales.')
        if company_id != self.env.company.id:
            raise ValidationError('La compañía activa cambió. Recargue el reporte antes de modificar los descuentos.')
        campos = {
            'iva': 'mastershop_descontar_iva',
            'renta': 'mastershop_descontar_renta',
        }
        if campo not in campos or type(valor) is not bool:
            raise ValidationError('Seleccione un descuento y un valor válido.')
        # A manager may change only these two settings in the active company.
        self.env.company.sudo().write({campos[campo]: valor})
        return self.get_deducciones()
