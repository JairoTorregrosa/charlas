---
name: margen-por-proyecto
description: Calcula el margen por proyecto y su cambio entre meses a partir de contabilidad.csv (PUC colombiano). Úsala cuando pregunten por margen, rentabilidad o utilidad por proyecto.
---

# Margen por proyecto

## Datos
`contabilidad.csv`: separador `;`, decimal con coma. Columnas clave: `Period` (6 = junio, 7 = julio), `AccountId`, `Debito`, `Credito`, `ProjectId`, `CostCenterName`.

## Reglas
- Ingreso = cuentas que empiezan por `4`: `Credito - Debito`.
- Costo = cuentas que empiezan por `6` o `7`: `Debito - Credito`.
- Margen = (ingreso - costo) / ingreso. Cambio = margen julio - margen junio, en puntos porcentuales.
- Proyecto sin ingreso en un mes: margen `null`, no lo inventes.

## Método
```
uv run --with pandas python3 - <<'PY'
import pandas as pd
df = pd.read_csv("contabilidad.csv", sep=";", decimal=",", dtype={"AccountId": str})
df["clase"] = df["AccountId"].str[0]
df["ingreso"] = (df["Credito"] - df["Debito"]).where(df["clase"] == "4", 0)
df["costo"] = (df["Debito"] - df["Credito"]).where(df["clase"].isin(["6", "7"]), 0)
g = df[df["Period"].isin([6, 7])].groupby(["ProjectId", "Period"])[["ingreso", "costo"]].sum()
g["margen"] = (g["ingreso"] - g["costo"]) / g["ingreso"]
m = g["margen"].unstack("Period")
m["cambio_pp"] = (m[7] - m[6]) * 100
print(m.round(3).sort_values("cambio_pp"))
PY
```

## Causa
Para explicar un cambio, compara por `AccountName` los costos de junio y julio del proyecto afectado. La nómina (cuentas `7205…`) suele ser la causa.
