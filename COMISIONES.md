# Configurar comisiones

Primero reinicie Odoo para cargar los nuevos archivos Python y después actualice
`analitica_mastershop` para registrar los modelos y las vistas. Actualizar desde la
pantalla sin reiniciar antes puede producir «External ID not found:
analitica_mastershop.model_mastershop_comision_regla».
En Analítica MasterShop → Porcentajes y grupos (o Comisiones → Porcentajes y grupos),
un usuario del grupo Analítica MasterShop / Administrador puede crear las reglas.
Los usuarios internos pueden consultarlas.

1. Cree una regla «Por vendedor» para cada empleado: por ejemplo, Ana al 5% y Juan al 10%.
   Indique la fecha desde la cual aplica; deje «Hasta» vacío si no tiene vencimiento.
2. Para una campaña, cree «Temporada para todos», indique porcentaje y fechas.
   Esta regla reemplaza los porcentajes individuales de esa compañía durante la temporada,
   incluyendo el primer y último día. Después se retoman las reglas individuales vigentes.
3. Para cambiar un porcentaje individual sin modificar períodos anteriores, cierre la regla
   anterior y cree otra con inicio al día siguiente. No se permiten fechas superpuestas
   para el mismo vendedor ni entre temporadas de la misma compañía.

El cálculo usa la fecha de cada factura contabilizada y el total con impuestos:
comisión de ventas menos comisión de devoluciones, menos las deducciones opcionales
y los descuentos/envíos manuales.
Cada documento redondea su comisión a los decimales de su moneda.
Las notas de crédito vinculadas a una factura usan la fecha de la factura original;
las notas independientes usan su propia fecha.

El reporte separa vendedor, compañía y moneda. Los descuentos/envíos se registran en
la moneda de la compañía y se descuentan una sola vez.
No se convierten importes entre monedas.

Los documentos sin regla vigente generan comisión cero y se señalan en la columna
«Documentos sin porcentaje» y el filtro «Falta configurar porcentaje».
Una regla explícita de 0% se considera configurada.
Configure también las fechas de las ventas históricas que necesite calcular.
El reporte incluye todos los documentos contabilizados del vendedor, como antes;
no constituye un registro de comisiones pagadas ni tiene cierre de liquidaciones.
Editar o borrar reglas recalcula los resultados históricos.

Ejemplo: ventas $1,000, devoluciones $100, ambas al 10%, descuentos $4:
comisión $90 y neto a liquidar $86.

## Validación

Se verificó la consulta SQL real en PostgreSQL 16 con datos ficticios para porcentajes
individuales, temporada, límites de fechas, devolución posterior, descuentos, varias
compañías/monedas, borradores, regla de 0% y documentos sin regla.
Se verificó la sintaxis de los archivos Python y XML.

Pruebas de integración Odoo incluidas en `tests/test_comision.py`:

```sh
odoo-bin -d BASE_PRUEBA -u analitica_mastershop --test-enable --test-tags /analitica_mastershop --stop-after-init
```

Estas pruebas requieren una instalación de Odoo con sus dependencias y base de prueba;
no se han ejecutado en la base operativa.

## Casillas generales de descuentos

En Comisiones aparecen IVA 13% y Renta 10%, independientes y opcionales.
Ambos se calculan sobre la comisión generada positiva, antes de descuentos manuales.
Al marcar o desmarcar una casilla se recalculan todos los vendedores de la compañía
activa. La configuración se guarda por compañía y afecta también el histórico.
Solo los administradores de Analítica MasterShop pueden modificar estas casillas.

Neto = comisión − IVA (si está marcado) − renta (si está marcada) − descuentos manuales.

Con $1,000 de comisión y ambas casillas activadas: IVA $130, renta $100, neto $770.
La renta es fija para todos los vendedores, sin tramos ni cuotas fijas.
C807 queda excluido del cálculo automático.

## Comisiones para grupos

La configuración abre tarjetas con el porcentaje, las personas y las fechas.
Al crear una regla puede elegir:

- **Un grupo de personas:** nombre el grupo, seleccione sus integrantes y escriba el porcentaje una sola vez.
- **Una persona:** conserve o configure una comisión individual.
- **Todos por temporada:** aplique un porcentaje general dentro de sus fechas.

Prioridad: temporada → regla individual → regla de grupo.
Una persona no puede tener dos reglas de grupo en fechas superpuestas.
La regla individual permite una excepción al porcentaje del grupo.
Los integrantes deben pertenecer a la compañía de la regla.
Editar los integrantes también recalcula las facturas históricas dentro de la vigencia.

Puede buscar integrantes y filtrar por grupos, individuales o temporadas, así como
agrupar las reglas por tipo o porcentaje. En el reporte, «Asignar %» abre una regla
para el vendedor cuyas facturas aún no tienen porcentaje, con una fecha inicial
sugerida a partir de su primera factura; revise la vigencia antes de guardar.
Las casillas de IVA y renta se muestran en una franja independiente de la búsqueda.

## Eliminar un descuento equivocado

Abra el historial del vendedor (icono de lista junto a Descontar) y pulse
**Eliminar descuento** en la fila correspondiente. Al confirmar, se borra solo
ese descuento, se cierra el historial y se recarga el reporte de comisiones.
El importe eliminado deja de restarse automáticamente del saldo del vendedor.
Ejemplo: quitar un descuento de $4 cambia el saldo de −$2.77 a $1.23.
