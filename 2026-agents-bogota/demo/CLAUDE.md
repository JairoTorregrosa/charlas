# Contexto del proyecto (demo D2)

Datos: `contabilidad.csv`, separador `;`, decimal con coma, columna `Period` (6 = junio, 7 = julio).
Reglas: ingresos = cuentas que empiezan por 4 (crédito − débito); costos = cuentas 6 y 7 (débito − crédito). Margen = (ingreso − costo) / ingreso.
Python: usa `uv run --with pandas python3 …` (pandas no está en el Python del sistema).
Respuesta corta, cabe en una pantalla: tabla por proyecto (junio, julio, cambio en puntos; máximo 8 filas), la causa principal en 2 frases, y el código esencial (máximo 10 líneas). Sin introducción ni cierre.
