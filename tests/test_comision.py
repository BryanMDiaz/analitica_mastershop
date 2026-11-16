from odoo import Command
from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged('post_install', '-at_install')
class TestMastershopComision(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.vendedor = cls.env['hr.employee'].create({
            'name': 'Comisionista de prueba', 'company_id': cls.env.company.id,
        })
        cls.reglas = cls.env['mastershop.comision.regla']

    def regla(self, porcentaje, **values):
        return self.reglas.create({
            'name': 'Regla de prueba', 'tipo': 'individual',
            'vendedor_id': self.vendedor.id, 'porcentaje': porcentaje,
            'fecha_inicio': '2026-01-01', **values,
        })

    def factura(self, fecha, monto, **values):
        move = self.env['account.move'].create({
            'move_type': 'out_invoice', 'partner_id': self.partner_a.id,
            'vendedor_id': self.vendedor.id, 'invoice_date': fecha,
            'invoice_line_ids': [Command.create({
                'name': 'Venta', 'quantity': 1, 'price_unit': monto,
                'account_id': self.company_data['default_account_revenue'].id,
                'tax_ids': [Command.clear()],
            })], **values,
        })
        move.action_post()
        return move

    def reporte(self):
        self.env.flush_all()
        self.env.invalidate_all()
        return self.env['mastershop.comision.reporte'].search([
            ('vendedor_id', '=', self.vendedor.id), ('company_id', '=', self.env.company.id),
        ])

    def test_temporada_y_devolucion(self):
        self.regla(5)
        self.regla(10, tipo='temporada', vendedor_id=False,
                   fecha_inicio='2026-06-01', fecha_fin='2026-06-30')
        self.factura('2026-05-31', 100)
        original = self.factura('2026-06-01', 100)
        self.factura('2026-06-30', 100)
        self.factura('2026-07-01', 100)
        self.factura('2026-07-02', 20, move_type='out_refund', reversed_entry_id=original.id)
        self.env['mastershop.comision.descuento'].create({
            'vendedor_id': self.vendedor.id, 'monto': 4, 'motivo': 'Envío',
        })
        report = self.reporte()
        self.assertEqual(report.total_comision, 28)
        self.assertEqual(report.total_neto, 24)
        self.assertEqual(report.sin_porcentaje, 0)

    def test_sin_regla_y_cero_explicito(self):
        self.factura('2026-01-01', 100)
        self.assertEqual(self.reporte().sin_porcentaje, 1)
        self.regla(0)
        report = self.reporte()
        self.assertEqual(report.sin_porcentaje, 0)
        self.assertEqual(report.total_comision, 0)

    def test_rechazar_solapamiento(self):
        self.regla(5, fecha_fin='2026-06-30')
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.regla(10, fecha_inicio='2026-06-30')
        self.regla(10, fecha_inicio='2026-07-01')

    def test_deducciones_sobre_comision_y_reversibles(self):
        self.regla(100)
        self.factura('2026-01-01', 1000)
        self.env.company.sudo().write({
            'mastershop_descontar_iva': True,
            'mastershop_descontar_renta': True,
        })
        report = self.reporte()
        self.assertEqual(report.total_iva, 130)
        self.assertEqual(report.total_renta, 100)
        self.assertEqual(report.total_neto, 770)
        self.env.company.sudo().write({
            'mastershop_descontar_iva': False,
            'mastershop_descontar_renta': False,
        })
        self.assertEqual(self.reporte().total_neto, 1000)

    def test_renta_fija_para_cualquier_monto(self):
        self.regla(100)
        self.factura('2026-01-01', 500)
        self.factura('2026-02-01', 500)
        self.env.company.sudo().mastershop_descontar_renta = True
        self.assertEqual(self.reporte().total_renta, 100)

    def test_casillas_requieren_administrador(self):
        from odoo.exceptions import AccessError
        from odoo.tests import new_test_user
        user = new_test_user(self.env, login='comision_lectura', groups='base.group_user')
        report = self.env['mastershop.comision.reporte'].with_user(user)
        with self.assertRaises(AccessError):
            report.set_deduccion(self.env.company.id, 'iva', True)

    def test_grupo_individual_y_temporada(self):
        otro = self.env['hr.employee'].create({
            'name': 'Segundo integrante', 'company_id': self.env.company.id,
        })
        self.regla(12, tipo='grupo', vendedor_id=False,
                   vendedor_ids=[Command.set((self.vendedor | otro).ids)])
        self.regla(15, vendedor_id=otro.id)
        self.regla(20, tipo='temporada', vendedor_id=False,
                   fecha_inicio='2026-06-01', fecha_fin='2026-06-30')
        self.factura('2026-01-01', 100)
        self.factura('2026-01-02', 100, vendedor_id=otro.id)
        self.factura('2026-06-01', 100)
        self.assertEqual(self.reporte().total_comision, 32)
        report_otro = self.env['mastershop.comision.reporte'].search([
            ('vendedor_id', '=', otro.id), ('company_id', '=', self.env.company.id),
        ])
        self.assertEqual(report_otro.total_comision, 15)

    def test_grupos_no_superponen_personas(self):
        self.regla(5, tipo='grupo', vendedor_id=False,
                   vendedor_ids=[Command.set(self.vendedor.ids)], fecha_fin='2026-06-30')
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.regla(10, tipo='grupo', vendedor_id=False,
                       vendedor_ids=[Command.set(self.vendedor.ids)], fecha_inicio='2026-06-30')
        self.regla(10, tipo='grupo', vendedor_id=False,
                   vendedor_ids=[Command.set(self.vendedor.ids)], fecha_inicio='2026-07-01')
        self.regla(15)  # An individual rule may override the group.
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.regla(5, tipo='grupo', vendedor_id=False)

    def test_eliminar_descuento_reintegra_importe(self):
        self.regla(8)
        self.factura('2026-01-01', 20)
        self.env.company.sudo().write({
            'mastershop_descontar_iva': True, 'mastershop_descontar_renta': True,
        })
        self.assertEqual(self.reporte().total_neto, 1.23)
        descuento = self.env['mastershop.comision.descuento'].create({
            'vendedor_id': self.vendedor.id, 'monto': 4, 'motivo': 'Registro equivocado',
        })
        self.assertEqual(self.reporte().total_neto, -2.77)
        result = descuento.action_eliminar_descuento()
        self.assertEqual(result['type'], 'ir.actions.act_window_close')
        self.assertFalse(descuento.exists())
        self.assertEqual(self.reporte().total_descuentos, 0)
        self.assertEqual(self.reporte().total_neto, 1.23)
