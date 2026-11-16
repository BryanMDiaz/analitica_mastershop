<div align="center">

<img src="static/description/icon.png" alt="Analítica MasterShop" width="110" />

# Analítica MasterShop

### Tus ventas, tus clientes y tus comisiones. En un solo lugar.

Un módulo para **Odoo 18** que conecta la operación comercial de MasterShop con un tablero de indicadores, reportes de ventas y gestión de comisiones.

![Odoo](https://img.shields.io/badge/Odoo-18.0-714B67?style=for-the-badge)
![Versión](https://img.shields.io/badge/Versión-18.0.1.3.1-2563EB?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Licencia](https://img.shields.io/badge/Licencia-LGPL--3-16A34A?style=for-the-badge)

[Funcionalidades](#-qué-puedes-hacer) · [Instalación](#-instalación) · [Comisiones](#-comisiones-con-reglas-claras) · [Pruebas](#-validación-y-pruebas)

</div>

---

## ✨ Qué puedes hacer

| Área | Funcionalidades |
| :--- | :--- |
| 📊 **Tablero de control** | Consulta indicadores por mes, compara la facturación con el período anterior y accede a las facturas desde el tablero. |
| 🛒 **Ventas y punto de venta** | Analiza información comercial e integra vendedores en los flujos de POS y facturación. |
| 👥 **Clientes MasterShop** | Identifica contactos con la etiqueta Mastershop y consulta sus facturas y pedidos. |
| 📦 **Inventario** | Explora productos con vistas de lista y tarjetas, filtros y búsqueda por nombre o referencia. |
| 💸 **Comisiones** | Configura porcentajes individuales, por grupo o por temporada, con fechas de vigencia. |
| 🧾 **Descuentos y deducciones** | Gestiona descuentos manuales y opciones generales de IVA y renta por compañía. |
| 🔐 **Permisos** | Utiliza los grupos Usuario y Administrador de Analítica MasterShop. |

## 🚀 Instalación

### Requisitos

- Una instalación operativa de **Odoo 18** con PostgreSQL.
- Acceso a una carpeta de módulos incluida en `addons_path`.
- Los módulos de Odoo declarados como dependencias: `base`, `mail`, `analytic`, `account`, `sale`, `stock`, `point_of_sale`, `hr` y `pos_hr`.

### 1. Descargar el módulo

Desde tu carpeta de módulos personalizados:

```bash
git clone https://github.com/BryanMDiaz/analitica_mastershop.git analitica_mastershop
```

La carpeta debe conservar el nombre **`analitica_mastershop`**, utilizado por los recursos y referencias del módulo.

### 2. Instalar en Odoo

1. Incluye la carpeta que contiene `analitica_mastershop` en el `addons_path` de tu configuración.
2. Reinicia el servicio de Odoo.
3. Activa el modo desarrollador y actualiza la lista de aplicaciones.
4. Busca **Analítica MasterShop** e instala el módulo.
5. Asigna los permisos correspondientes y abre la aplicación.

También puedes instalar desde la línea de comandos, ajustando las rutas y el nombre de base de datos:

```bash
odoo-bin -c /ruta/odoo.conf -d BASE_DATOS -i analitica_mastershop --stop-after-init
```

### Actualizar una instalación existente

Después de descargar cambios, reinicia Odoo para cargar los archivos Python y actualiza el módulo:

```bash
odoo-bin -c /ruta/odoo.conf -d BASE_DATOS -u analitica_mastershop --stop-after-init
```

Al terminar, inicia nuevamente el servicio de Odoo.

## 🧭 Primeros pasos

1. **Configura los accesos:** asigna el grupo Usuario o Administrador de Analítica MasterShop.
2. **Revisa los datos comerciales:** etiquetas de clientes, categorías de productos, puntos de venta y vendedores asociados a las facturas.
3. **Define los porcentajes:** abre **Porcentajes y grupos** y configura integrantes, porcentajes y vigencias.
4. **Consulta resultados:** explora Tablero de Control, Clientes MasterShop, Reportes de Ventas, Inventario y Comisiones.

> El módulo contiene filtros y criterios específicos de MasterShop. Revisa los nombres, categorías y compañías configurados antes de utilizarlo en otra operación.

## 💸 Comisiones con reglas claras

Los porcentajes se resuelven con esta prioridad:

**Temporada → Regla individual → Regla de grupo**

- Define porcentajes con fecha de inicio y fin opcional.
- Calcula sobre documentos contabilizados y sus importes con impuestos.
- Descuenta las devoluciones y los ajustes manuales correspondientes.
- Identifica documentos sin porcentaje configurado.
- Consulta resultados separados por vendedor, compañía y moneda, sin conversión entre monedas.

**Ejemplo:** ventas de $1,000 y devoluciones de $100 al 10% generan $90 de comisión. Con $4 de descuentos manuales, el neto es **$86** si las deducciones opcionales están desactivadas.

> Editar reglas o integrantes puede recalcular resultados históricos. El reporte no lleva un registro de comisiones pagadas ni cierres de liquidación.

Consulta la [guía completa de comisiones](COMISIONES.md) para conocer las deducciones opcionales de IVA 13% y renta 10%, las vigencias, excepciones y el historial de descuentos.

## 🧩 Estructura del proyecto

```text
analitica_mastershop/
├── models/               # Modelos, indicadores y lógica de comisiones
├── security/             # Grupos, permisos y reglas de acceso
├── static/
│   ├── description/      # Icono de la aplicación
│   └── src/              # Componentes de dashboard, comisiones y POS
├── tests/                # Pruebas de integración de comisiones
├── views/                # Vistas, acciones y menús de Odoo
├── __init__.py
├── __manifest__.py       # Versión, dependencias y recursos del módulo
├── COMISIONES.md         # Guía funcional de comisiones
└── README.md
```

**Tecnologías:** Python · ORM de Odoo · PostgreSQL/SQL · JavaScript/OWL · XML/QWeb · SCSS.

## 🧪 Validación y pruebas

El repositorio incluye pruebas de integración para comisiones en `tests/test_comision.py`. Ejecútalas en una base de pruebas con Odoo y sus dependencias disponibles:

```bash
odoo-bin -c /ruta/odoo.conf -d BASE_PRUEBA -u analitica_mastershop --test-enable --test-tags /analitica_mastershop --stop-after-init
```

Estas pruebas requieren el entorno de Odoo; no se ejecutan como pruebas Python independientes.

## 🤝 Contribuciones

Para reportar un problema o proponer una mejora, abre un [issue](https://github.com/BryanMDiaz/analitica_mastershop/issues) e incluye la versión de Odoo, los pasos para reproducirlo y el comportamiento esperado. Los cambios pueden proponerse mediante pull requests.

## 📄 Autoría y licencia

**Autor del módulo:** Velatek, según `__manifest__.py`.

**Licencia declarada:** LGPL-3, según `__manifest__.py`.

---

<div align="center">

**MasterShop · Información para entender tu operación y decidir mejor.**

</div>
