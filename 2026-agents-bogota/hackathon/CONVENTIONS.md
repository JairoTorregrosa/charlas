# CONVENTIONS · reglas contables y de cálculo del golden

Toda golden (`golden/v1/qNN.json`) y todo `tasks/qNN/solution/solve.py` aplica estas
convenciones y las cita por número (`CONV §2.1`). Los puntos marcados **[verificar]**
son decisiones tomadas por el equipo del benchmark que Quick (finanzas) debe confirmar
antes de pasar una golden a `status: approved`; hasta entonces el juez las trata como
la referencia y acepta respuestas que declaren explícitamente una convención distinta
(ver §7).

Fuente metodológica: `Caso Financiero.docx` (clasificación de cuentas, estructura del
informe, variación, semáforo, uso de nómina y ausencias). Perfil de los datos:
`golden/PROFILE.md`.

## 1. Carga de datos

1.1 **CSV contable** `MAYO-JUNIO-JULIO 2026.csv`: `sep=';'`, decimal `','`, todas las
columnas como texto y luego `Debito`/`Credito` a float; `Date` con formato
`dd/mm/yyyy HH:MM:SS`. Se usa el loader canónico `bench.data.load_ledger()`.
Los códigos (`DocumentId`, `ConceptId`, `Module`…) traen espacios de relleno: se
normalizan con `strip()` siempre.

1.2 **Filas corridas.** Dos filas (Period 6, ProjectId 955, cuentas 73551501 y 73550501)
llegan con las columnas desplazadas desde el origen (`CostCenterName='0'`,
`State≠'P'`). Se **conservan**: su `AccountId`, `Debito`, `ProjectId`, `Period` y
`CostCenterId=2002` son correctos. No se "limpian" borrándolas.

1.3 **Línea / GERENCIA.** La "línea" (y la GERENCIA del informe) es el centro de costo
**por id**: `CostCenterId` → `bench.data.LINES` (2001 LONG HAUL, 2002 WAREHOUSE,
2003 FIRST MILE, 3001 LAST MILE COLOMBIA, 4001 GERENCIAS, 5001 COURIER COLOMBIA,
1001 GLOBAL COLOMBIA). Nunca por `CostCenterName`. **[verificar]**: que GERENCIA del
informe de Quick coincida con esta agrupación.

1.4 **Proyecto.** `ProjectId` tal cual; etiqueta del informe `"Proyecto NNNN"`. Un
proyecto puede aparecer en más de una línea (ver PROFILE §1.3); en el informe por
proyecto se agrupa por `(línea, proyecto)`.

1.5 **Nómina** (`ACUMULADO …xlsx`, hoja 0): una fila por empleado × concepto con
`Debit`/`Credit`/`Value`, `Period` del archivo. El archivo de julio es
**"ACUMULADO INICIAL … 03.08.2026"**: preliminar; toda cifra de julio derivada de nómina
lleva caveat. **Ausencias** (`Listado_de_Ausencias …xlsx`, hoja `' Data'`): una fila por
novedad con `DateInitial`/`DateFinal` (`dd/mm/yyyy`), `Quantity` (días), `ProjectId`.
Los listados se solapan entre meses (abr–may, may–jun, jun–jul): una novedad se asigna
al mes por `DateInitial` y se deduplica por (`ClientId`, `ConceptId`, `DateInitial`,
`DateFinal`).

1.6 **Empleado → proyecto.** La nómina no trae `ProjectId`. El vínculo se toma del CSV:
filas con `DocumentId='NM'` (o `AP`, aportes) tienen `ClientId` = empleado (`7000000NN`,
"Empleado NN") y `ProjectId`. El listado de ausencias trae `ProjectId` directo.

## 2. Ingreso, costo, gasto, margen

2.1 **Ingreso** de un grupo y mes = Σ(`Credito` − `Debito`) de las filas con
`AccountId` que empieza por `4`, `Period` = mes. Incluye TODAS las cuentas 4 (41 ventas,
42 otros ingresos: reintegros, incapacidades, diferencia en cambio…), porque el docx
dice "total de ingresos registrados en cuentas contables de la clase 4". **[verificar]**
si Quick excluye 42xx del INGRESO del informe.

2.2 **Costo** = Σ(`Debito` − `Credito`) de cuentas `6*` y `7*`, `Period` = mes.

2.3 **Gasto** = Σ(`Debito` − `Credito`) de cuentas `5*`. Se reporta aparte y **NO entra
al margen** de proyecto/línea (el docx define COSTO como 6 y 7). Casi todo el gasto vive
en la línea GERENCIAS (4001). **[verificar]** con Quick.

2.4 **Margen** (`%`) = (Ingreso − Costo) / Ingreso. Si Ingreso ≤ 0 → margen `null` y se
reporta el costo con caveat; nunca se fuerza un número. Se expresa en **puntos
porcentuales con 2 decimales** (ej. `17.41`).

2.5 **Utilidad** (informe) = Ingreso julio − Costo julio. **Variación ingreso** =
Ingreso julio − Ingreso junio.

2.6 **Variación** de rentabilidad = margen julio − margen junio, en **pp**.
**Semáforo**: 🟢 Aumenta si variación > +1.0 pp; 🔴 Disminuye si < −1.0 pp; 🟡 Se
mantiene si |variación| ≤ 1.0 pp. **[verificar]** umbral (el docx dice "variación
relevante" sin cifra). Si alguno de los márgenes es `null`: observación `n/a`.

2.7 **Evolución en tres meses** (q01): se ordena por (margen julio − margen mayo) en pp,
y se reporta también jun→jul para confirmar que la tendencia no es un rebote. Se excluyen
líneas con ingreso < 0.5 % del total (COURIER, GLOBAL) y GERENCIAS (sin costo 6/7:
margen 100 % por construcción) del ranking, pero se mencionan.

2.8 **Redondeo**: COP sin decimales en la respuesta; cálculos en float completo; margen
2 decimales. Tolerancias del juez en cada golden (`tolerance`), por defecto COP ±0.5 %
relativo y margen ±0.2 pp.

## 3. Tabla base del informe (`golden/v1/base-table.csv`)

Columnas: `GERENCIA, PROYECTO, NOMBRE, INGRESO_JUN, COSTO_JUN, MARGEN_JUN, INGRESO_JUL,
COSTO_JUL, MARGEN_JUL, VARIACION_PP, OBSERVACION, VARIACION_INGRESO, UTILIDAD_JUL`.
Una fila por (línea, proyecto) con movimiento en junio o julio en cuentas 4/6/7. Se
genera con `tasks/base-table/solve.py` y es la referencia de cifras para q01/q06/q07.

## 4. "Facturación real" (q04) **[verificar — prioridad alta]**

La clase 4 mezcla documentos de naturaleza distinta (PROFILE §1.5):

| DocumentId | Qué es (según nombres de cuenta y `Observation`) | Trato |
|---|---|---|
| `FC` | Factura de venta emitida (cuenta 4145/4135/4155…) | **facturación** |
| `DV` | Devolución / nota crédito sobre factura (cuentas 4175 "DEVOL…") | **resta** de la facturación |
| `NC`, `NF`, `NB`, `DB` | notas menores | se suman con su signo contable; se listan |
| `PI` | Provisión de ingreso (cuenta 41709501/02 "PROVISION DE INGRESO … QUICK HELP") | **no** es facturación: estimación de ingreso aún no facturado |
| `RI` | Reversión de provisión (misma cuenta, débito) | **no** es facturación |
| `NK` | Nota contable / reclasificación (débito y crédito) | no es facturación; se informa |
| `CP`, `RC`, `CE`, `AB`… | causaciones, recibos, egresos en cuentas 42xx y 4135 | otros ingresos, no facturación |

Definición golden: **facturación real del mes = Σ crédito de `FC` − Σ débito de `DV`
(y notas `NC/NF/NB/DB` con su signo) en cuentas 4, por `Period`**. Se reportan además,
para la misma tabla: (a) ingreso contable neto de clase 4 (CONV §2.1), (b) provisiones
`PI` y reversiones `RI` del mes, (c) la diferencia entre ingreso contable y facturación.
Una entrega que use (a) y lo declare obtiene crédito parcial (§7).

## 5. "Gasto corriente vs ajuste retroactivo" (q05) **[verificar — prioridad alta]**

`Date` siempre cae en el mes de `Period` (PROFILE §1): el criterio temporal no sirve.
Criterio golden de **retroactivo** para una fila de egreso (clases 5, 6, 7) en
`Period = m`:

- `Observation` cita explícitamente un mes anterior a `m` (nombre completo o
  abreviatura: ENERO…ABRIL/MAY… , o un año < 2026), **o**
- `Observation` contiene una palabra de reversión/ajuste de período (`REV`, `REVR`,
  `REVREM`, `REVERSION`, `AJUSTE`, `RECLA`/`RECLASIF`, `CORRECCION`, `RETROACTIVO`)
  **sin** citar el mes corriente, **o**
- la fila es una reversión de provisión del mes anterior (crédito en cuenta de
  costo/gasto con `Observation` de provisión y mes anterior).

Todo lo demás es **corriente** (incluidas las provisiones del propio mes: "PROV … JUNIO"
en `Period 6`). La partición se calcula sobre el **neto** (`Debito − Credito`) y se
reporta por separado para **gasto (5)**, que es la lectura literal de la pregunta, y para
**costo (6+7)** como tabla complementaria; el total (5+6+7) se da como tercera lectura.
El golden deja escrito el regex exacto y el conteo de filas por criterio, y lista los 10
`Observation` más frecuentes de cada bucket para que Quick pueda validar.

## 6. Novedades por proyecto (q06, q07)

6.1 Métricas jun/jul del proyecto (CONV §2) y variación en pp.
6.2 Descomposición de la variación de **costo** por cuenta (`AccountId`/`AccountName`)
y por `ConceptId`/`DocumentId`, top-N por |Δ|; y de **ingreso** por cuenta y documento
(FC/PI/RI/DV).
6.3 Cruce con nómina: empleados del proyecto (CONV §1.6) presentes en mayo/junio/julio;
altas y bajas (aparece/desaparece entre meses); conceptos de nómina con mayor Δ
(vacaciones, incapacidades, horas extra, retiros/liquidaciones).
6.4 Cruce con ausencias: novedades del `ProjectId` por mes (`DateInitial`), por concepto,
con días.
6.5 Cada "novedad" del golden lleva: fuente (archivo + filtro), cifra, signo del efecto
en margen y si es causa principal o secundaria.

## 7. Cómo trata el juez una convención distinta

Una entrega que use una convención distinta a la de aquí (p. ej. incluir gasto 5 en el
margen, excluir 42xx, umbral 0.5 pp, otra definición de facturación) **no se descalifica
si la declara explícitamente** y sus cifras son consistentes con esa declaración: el
`outcome_exact` se evalúa contra la golden (fallará) pero `outcome_judge` y `honesty`
pueden puntuar alto. Una entrega que **no** declara su convención y no cuadra con la
golden puntúa bajo en ambos.
