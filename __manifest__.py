# -*- coding: utf-8 -*-
{
    'name': 'Analítica MasterShop',
    'version': '18.0.1.3.1',
    'summary': 'Módulo de Analítica y Gestión de Ventas para MasterShop',
    'description': """
Módulo de Analítica MasterShop
==============================
Este módulo permite la gestión y el análisis integral de ventas y clientes de MasterShop:
- Análisis exclusivo de clientes etiquetados con Mastershop.
- Reportes de ventas exclusivos para la sucursal GRUPO 2 S.A. DE C.V.
- Métricas gráficas mensuales y análisis de facturas con productos MasterShop, Herramientas Master Shop y MASTER.
    """,
    'category': 'Sales/Sales',
    'author': 'Velatek',
    'website': 'https://www.velatek.com',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',
        'analytic',
        'account',
        'sale',
        'stock',
        'point_of_sale',
        'hr',
        'pos_hr',
    ],
    'data': [
        'security/analitica_mastershop_security.xml',
        'security/ir.model.access.csv',
        'views/analitica_mastershop_views.xml',
        'views/clientes_mastershop_views.xml',
        'views/reportes_ventas_views.xml',
        'views/inventario_mastershop_views.xml',
        'views/pos_order_views.xml',
        'views/comision_views.xml',
        'views/dashboard_views.xml',
        'views/menu_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'analitica_mastershop/static/src/comisiones/comision_list.js',
            'analitica_mastershop/static/src/comisiones/comision_list.scss',
            'analitica_mastershop/static/src/comisiones/comision_list.xml',
            'analitica_mastershop/static/src/dashboard/dashboard.scss',
            'analitica_mastershop/static/src/dashboard/dashboard.js',
            'analitica_mastershop/static/src/dashboard/dashboard.xml',
        ],
        'point_of_sale._assets_pos': [
            'analitica_mastershop/static/src/**/*',
            ('remove', 'analitica_mastershop/static/src/comisiones/**/*'),
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}
