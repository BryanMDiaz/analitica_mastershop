# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import date, timedelta


class AnaliticaMastershop(models.Model):
    _inherit = 'analitica.mastershop'

    @api.model
    def get_dashboard_kpis(self, selected_year=None, selected_month=None):
        """
        Retorna las métricas y datos consolidados para el Tablero de Control / Dashboard de MasterShop.
        Incluye ventas de POS y Contabilidad, Clientes, Comisiones y evolución de últimos 12 meses.
        """
        cr = self.env.cr
        today = fields.Date.today()
        year = int(selected_year) if selected_year else today.year
        month = int(selected_month) if selected_month else today.month

        first_this_month = date(year, month, 1)
        if month == 12:
            last_this_month = date(year, 12, 31)
        else:
            last_this_month = date(year, month + 1, 1) - timedelta(days=1)

        last_month_end = first_this_month - timedelta(days=1)
        first_last_month = last_month_end.replace(day=1)
        first_year = date(year, 1, 1)

        month_names = {
            1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
            5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
            9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
        }
        mes_actual_nombre = f"{month_names[month]} {year}"
        mes_anterior_nombre = f"{month_names[last_month_end.month]} {last_month_end.year}"

        # 1. Facturación Mes Seleccionado
        cr.execute("""
            SELECT 
                COALESCE(SUM(amount_untaxed_signed), 0.0) as subtotal,
                COALESCE(SUM(amount_total_signed), 0.0) as total_con_iva,
                COUNT(id) as cant_facturas
            FROM account_move
            WHERE move_type IN ('out_invoice', 'out_refund')
              AND state = 'posted'
              AND (
    es_mastershop = True 
    OR id IN (
        SELECT po.account_move 
        FROM pos_order po
        JOIN pos_session s ON s.id = po.session_id
        JOIN pos_config c ON c.id = s.config_id
        WHERE c.name ILIKE '%%mastershop%%' AND po.account_move IS NOT NULL
    )
    OR (vendedor_id IS NOT NULL AND move_type IN ('out_invoice', 'out_refund'))
)
              AND invoice_date >= %s AND invoice_date <= %s
        """, (first_this_month, last_this_month))
        row_now = cr.dictfetchone() or {}
        mes_actual_subtotal = float(row_now.get('subtotal') or 0.0)
        mes_actual_total = float(row_now.get('total_con_iva') or 0.0)
        facturas_mes = int(row_now.get('cant_facturas') or 0)

        # 2. Facturación Mes Anterior
        cr.execute("""
            SELECT 
                COALESCE(SUM(amount_untaxed_signed), 0.0) as subtotal,
                COALESCE(SUM(amount_total_signed), 0.0) as total_con_iva,
                COUNT(id) as cant_facturas
            FROM account_move
            WHERE move_type IN ('out_invoice', 'out_refund')
              AND state = 'posted'
              AND (
    es_mastershop = True 
    OR id IN (
        SELECT po.account_move 
        FROM pos_order po
        JOIN pos_session s ON s.id = po.session_id
        JOIN pos_config c ON c.id = s.config_id
        WHERE c.name ILIKE '%%mastershop%%' AND po.account_move IS NOT NULL
    )
    OR (vendedor_id IS NOT NULL AND move_type IN ('out_invoice', 'out_refund'))
)
              AND invoice_date >= %s AND invoice_date <= %s
        """, (first_last_month, last_month_end))
        row_prev = cr.dictfetchone() or {}
        mes_anterior_subtotal = float(row_prev.get('subtotal') or 0.0)
        mes_anterior_total = float(row_prev.get('total_con_iva') or 0.0)
        facturas_mes_anterior = int(row_prev.get('cant_facturas') or 0)

        # Variación %
        if mes_anterior_subtotal > 0:
            var_pct = round(((mes_actual_subtotal - mes_anterior_subtotal) / mes_anterior_subtotal) * 100.0, 1)
            var_positiva = var_pct >= 0
        else:
            var_pct = 100.0 if mes_actual_subtotal > 0 else 0.0
            var_positiva = True

        # 3. Comisiones del Mes
        cr.execute("""
            SELECT 
                COALESCE(SUM(CASE WHEN move_type = 'out_invoice' THEN amount_total ELSE -amount_total END), 0.0) as ventas_comision
            FROM account_move
            WHERE move_type IN ('out_invoice', 'out_refund')
              AND state = 'posted'
              AND vendedor_id IS NOT NULL
              AND invoice_date >= %s AND invoice_date <= %s
        """, (first_this_month, last_this_month))
        ventas_comision_mes = float(cr.fetchone()[0] or 0.0)

        # Descuentos aplicados en el mes
        cr.execute("""
            SELECT COALESCE(SUM(monto), 0.0)
            FROM mastershop_comision_descuento
            WHERE fecha >= %s AND fecha <= %s
        """, (first_this_month, last_this_month))
        descuentos_mes = float(cr.fetchone()[0] or 0.0)
        comisiones_neto_mes = ventas_comision_mes - descuentos_mes

        # 4. Total Acumulado Año
        cr.execute("""
            SELECT 
                COALESCE(SUM(amount_untaxed_signed), 0.0) as subtotal,
                COALESCE(SUM(amount_total_signed), 0.0) as total_con_iva,
                COUNT(id) as cant_facturas
            FROM account_move
            WHERE move_type IN ('out_invoice', 'out_refund')
              AND state = 'posted'
              AND (
    es_mastershop = True 
    OR id IN (
        SELECT po.account_move 
        FROM pos_order po
        JOIN pos_session s ON s.id = po.session_id
        JOIN pos_config c ON c.id = s.config_id
        WHERE c.name ILIKE '%%mastershop%%' AND po.account_move IS NOT NULL
    )
    OR (vendedor_id IS NOT NULL AND move_type IN ('out_invoice', 'out_refund'))
)
              AND invoice_date >= %s AND invoice_date <= %s
        """, (first_year, last_this_month))
        row_year = cr.dictfetchone() or {}
        anual_subtotal = float(row_year.get('subtotal') or 0.0)
        anual_total = float(row_year.get('total_con_iva') or 0.0)

        # 5. Clientes y Retención MasterShop
        cr.execute("""
            SELECT p.id, MAX(am.invoice_date) as ultima_compra
            FROM res_partner p
            JOIN res_partner_res_partner_category_rel rel ON rel.partner_id = p.id
            JOIN res_partner_category c ON c.id = rel.category_id
            LEFT JOIN account_move am ON am.partner_id = p.id AND (
    am.es_mastershop = true 
    OR am.id IN (
        SELECT po.account_move 
        FROM pos_order po
        JOIN pos_session s ON s.id = po.session_id
        JOIN pos_config c ON c.id = s.config_id
        WHERE c.name ILIKE '%%mastershop%%' AND po.account_move IS NOT NULL
    )
    OR am.vendedor_id IS NOT NULL
) AND am.state = 'posted' 
            WHERE c.name::text ILIKE '%%mastershop%%'
            GROUP BY p.id
        """)
        clientes_rows = cr.fetchall()
        total_clientes = len(clientes_rows)
        activos_30 = 0
        alerta_31_90 = 0
        riesgo_90 = 0

        for cid, ult_compra in clientes_rows:
            if not ult_compra:
                riesgo_90 += 1
            else:
                dias = (today - ult_compra).days
                if dias <= 30:
                    activos_30 += 1
                elif dias <= 90:
                    alerta_31_90 += 1
                else:
                    riesgo_90 += 1

        # 6. Top 5 Clientes MasterShop con Mayor Gasto Histórico
        cr.execute("""
            SELECT 
                p.id,
                p.name,
                COUNT(am.id) as facturas,
                COALESCE(SUM(am.amount_total_signed), 0.0) as total_facturado,
                MAX(am.invoice_date) as ultima_fecha
            FROM res_partner p
            JOIN account_move am ON am.partner_id = p.id
            WHERE am.es_mastershop = True AND am.state = 'posted'
            GROUP BY p.id, p.name
            ORDER BY total_facturado DESC
            LIMIT 5
        """)
        top_clientes = []
        for r in cr.dictfetchall():
            top_clientes.append({
                'id': r['id'],
                'name': r['name'],
                'facturas': r['facturas'],
                'total_facturado': r['total_facturado'],
                'total_fmt': f"${r['total_facturado']:,.2f}",
                'ultima_fecha': r['ultima_fecha'].strftime('%d/%m/%Y') if r['ultima_fecha'] else 'Sin compras',
            })

        # 7. Top Vendedores Comisionistas
        cr.execute("""
            SELECT 
                e.id,
                e.name,
                COUNT(am.id) as facturas,
                COALESCE(SUM(CASE WHEN am.move_type = 'out_invoice' THEN am.amount_total ELSE -am.amount_total END), 0.0) as total_ventas
            FROM hr_employee e
            JOIN account_move am ON am.vendedor_id = e.id
            WHERE am.state = 'posted'
            GROUP BY e.id, e.name
            ORDER BY total_ventas DESC
            LIMIT 5
        """)
        top_vendedores = []
        for r in cr.dictfetchall():
            emp_id = r['id']
            # Descuentos del empleado
            cr.execute("SELECT COALESCE(SUM(monto), 0.0) FROM mastershop_comision_descuento WHERE vendedor_id = %s", (emp_id,))
            desc = float(cr.fetchone()[0] or 0.0)
            neto = float(r['total_ventas']) - desc
            top_vendedores.append({
                'id': emp_id,
                'name': r['name'],
                'facturas': r['facturas'],
                'total_ventas_fmt': f"${r['total_ventas']:,.2f}",
                'descuentos_fmt': f"${desc:,.2f}",
                'neto_fmt': f"${neto:,.2f}",
            })

        # 8. Top 10 Productos Más Vendidos de MasterShop (Filtrados por Mes Seleccionado)
        cr.execute("""
            SELECT 
                COALESCE(
                    NULLIF(TRIM(SPLIT_PART(l.name, E'\\n', 2)), ''),
                    NULLIF(TRIM(SPLIT_PART(l.name, E'\\n', 1)), ''),
                    pt.name->>'es_ES',
                    pt.name->>'en_US'
                ) as producto,
                COALESCE(pp.default_code, '') as codigo,
                SUM(l.quantity) as cantidad,
                SUM(l.price_subtotal) as subtotal,
                SUM(l.price_total) as total
            FROM account_move_line l
            JOIN account_move am ON am.id = l.move_id
            LEFT JOIN product_product pp ON pp.id = l.product_id
            LEFT JOIN product_template pt ON pt.id = pp.product_tmpl_id
            WHERE am.move_type IN ('out_invoice', 'out_refund')
              AND am.state = 'posted'
              AND l.display_type = 'product'
              AND (
                  am.es_mastershop = True 
                  OR am.id IN (
                      SELECT p2.account_move 
                      FROM pos_order p2
                      JOIN pos_session s2 ON s2.id = p2.session_id
                      JOIN pos_config c2 ON c2.id = s2.config_id
                      WHERE c2.name ILIKE '%%mastershop%%' AND p2.account_move IS NOT NULL
                  )
                  OR (am.vendedor_id IS NOT NULL AND am.move_type IN ('out_invoice', 'out_refund'))
              )
              AND am.invoice_date >= %s AND am.invoice_date <= %s
            GROUP BY 1, 2
            ORDER BY cantidad DESC, total DESC
            LIMIT 10
        """, (first_this_month, last_this_month))
        top_productos = []
        for r in cr.dictfetchall():
            top_productos.append({
                'nombre': r['producto'] or 'Herramienta / Producto',
                'codigo': r['codigo'] or '',
                'cantidad': int(r['cantidad'] or 0),
                'subtotal_fmt': f"${float(r['subtotal'] or 0.0):,.2f}",
                'total_fmt': f"${float(r['total'] or 0.0):,.2f}",
            })

        # 9. Evolución Histórica de Ventas (Últimos 12 Meses)
        historico_mensual = []
        curr_y = today.year
        curr_m = today.month
        available_months = []

        for i in range(12):
            hist_date_first = date(curr_y, curr_m, 1)
            if curr_m == 12:
                hist_date_last = date(curr_y, 12, 31)
            else:
                hist_date_last = date(curr_y, curr_m + 1, 1) - timedelta(days=1)

            nombre_periodo = f"{month_names[curr_m]} {curr_y}"
            key = f"{curr_y}-{curr_m}"
            available_months.append({
                'key': key,
                'nombre': nombre_periodo,
                'selected': (curr_y == year and curr_m == month),
            })

            cr.execute("""
                SELECT 
                    COALESCE(SUM(amount_untaxed_signed), 0.0) as subtotal,
                    COALESCE(SUM(amount_total_signed), 0.0) as total_con_iva,
                    COUNT(id) as facturas
                FROM account_move
                WHERE move_type IN ('out_invoice', 'out_refund')
                  AND state = 'posted'
                  AND (
    es_mastershop = True 
    OR id IN (
        SELECT po.account_move 
        FROM pos_order po
        JOIN pos_session s ON s.id = po.session_id
        JOIN pos_config c ON c.id = s.config_id
        WHERE c.name ILIKE '%%mastershop%%' AND po.account_move IS NOT NULL
    )
    OR (vendedor_id IS NOT NULL AND move_type IN ('out_invoice', 'out_refund'))
)
                  AND invoice_date >= %s AND invoice_date <= %s
            """, (hist_date_first, hist_date_last))
            h_row = cr.dictfetchone() or {}
            subt = float(h_row.get('subtotal') or 0.0)
            tot_iva = float(h_row.get('total_con_iva') or 0.0)
            facts = int(h_row.get('facturas') or 0)

            # Promedio por factura
            promedio = (tot_iva / facts) if facts > 0 else 0.0

            historico_mensual.append({
                'periodo': nombre_periodo,
                'year': curr_y,
                'month': curr_m,
                'facturas': facts,
                'subtotal': subt,
                'subtotal_fmt': f"${subt:,.2f}",
                'total_con_iva': tot_iva,
                'total_con_iva_fmt': f"${tot_iva:,.2f}",
                'promedio_fmt': f"${promedio:,.2f}",
            })

            # Retroceder un mes
            if curr_m == 1:
                curr_m = 12
                curr_y -= 1
            else:
                curr_m -= 1

        # Cálculo de Proporción POS vs Contabilidad Directa en el mes actual
        cr.execute("""
            SELECT 
                COALESCE(SUM(CASE WHEN po.id IS NOT NULL THEN am.amount_total_signed ELSE 0 END), 0.0) as ventas_pos,
                COALESCE(SUM(CASE WHEN po.id IS NULL THEN am.amount_total_signed ELSE 0 END), 0.0) as ventas_conta
            FROM account_move am
            LEFT JOIN pos_order po ON po.account_move = am.id
            WHERE am.move_type IN ('out_invoice', 'out_refund')
              AND am.state = 'posted'
              AND (
                  am.es_mastershop = True 
                  OR am.id IN (
                      SELECT p2.account_move 
                      FROM pos_order p2
                      JOIN pos_session s2 ON s2.id = p2.session_id
                      JOIN pos_config c2 ON c2.id = s2.config_id
                      WHERE c2.name ILIKE '%%mastershop%%' AND p2.account_move IS NOT NULL
                  )
                  OR (am.vendedor_id IS NOT NULL AND am.move_type IN ('out_invoice', 'out_refund'))
              )
              AND am.invoice_date >= %s AND am.invoice_date <= %s
        """, (first_this_month, last_this_month))
        chan_row = cr.dictfetchone() or {}
        pos_ventas = float(chan_row.get('ventas_pos') or 0.0)
        conta_ventas = float(chan_row.get('ventas_conta') or 0.0)
        tot_chan = pos_ventas + conta_ventas
        pct_pos = round((pos_ventas / tot_chan * 100.0), 1) if tot_chan > 0 else 50.0
        pct_conta = round((conta_ventas / tot_chan * 100.0), 1) if tot_chan > 0 else 50.0

        return {
            'selected_year': year,
            'selected_month': month,
            'selected_period': mes_actual_nombre,
            'available_months': available_months,
            'historico_mensual': historico_mensual,
            'mes_actual': {
                'nombre': mes_actual_nombre,
                'subtotal': mes_actual_subtotal,
                'subtotal_fmt': f"${mes_actual_subtotal:,.2f}",
                'total': mes_actual_total,
                'total_fmt': f"${mes_actual_total:,.2f}",
                'facturas': facturas_mes,
                'pos_ventas_fmt': f"${pos_ventas:,.2f}",
                'conta_ventas_fmt': f"${conta_ventas:,.2f}",
                'pct_pos': pct_pos,
                'pct_conta': pct_conta,
            },
            'mes_anterior': {
                'nombre': mes_anterior_nombre,
                'subtotal': mes_anterior_subtotal,
                'subtotal_fmt': f"${mes_anterior_subtotal:,.2f}",
                'total_fmt': f"${mes_anterior_total:,.2f}",
                'facturas': facturas_mes_anterior,
            },
            'variacion': {
                'pct': abs(var_pct),
                'positiva': var_positiva,
            },
            'total_anual': {
                'anio': year,
                'monto': anual_total,
                'monto_fmt': f"${anual_total:,.2f}",
                'subtotal_fmt': f"${anual_subtotal:,.2f}",
            },
            'comisiones': {
                'ventas_comision_fmt': f"${ventas_comision_mes:,.2f}",
                'descuentos_fmt': f"${descuentos_mes:,.2f}",
                'neto_fmt': f"${comisiones_neto_mes:,.2f}",
            },
            'clientes_salud': {
                'total': total_clientes,
                'activos': activos_30,
                'alerta': alerta_31_90,
                'riesgo': riesgo_90,
            },
            'top_clientes': top_clientes,
            'top_vendedores': top_vendedores,
            'top_productos': top_productos,
        }

