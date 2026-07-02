# Dashboard BI — ORAD · Gobierno Regional de Lambayeque

Dashboard web de ejecución presupuestal de inversiones del **Pliego 452 - GORE Lambayeque**, construido en un único `index.html` (HTML + JavaScript + Chart.js + SheetJS), publicado vía GitHub Pages. Funciona de forma idéntica abriéndolo por doble clic (`file://`) o desde la web.

**Elaborado por:** ORPMI — Oficina Regional de Programación Multianual de Inversiones
**Fuente de datos:** Consulta Amigable MEF · [apps5.mineco.gob.pe](https://apps5.mineco.gob.pe/transparencia/Navegador/default.aspx)
**Dashboard en vivo:** https://jdrq.github.io/orad-dashboard/

---

## Contenido del Dashboard

| Bloque | Descripción |
|--------|-------------|
| Bloque 1 | KPIs financieros del Pliego (PIM, Certificación, Compromiso, Devengado) |
| Bloque 2 | Ranking nacional de los 26 Gobiernos Regionales |
| Bloque 3 | Ejecución por Unidad Ejecutora |
| Bloque 6 | Ejecución por Rubro / Fuente de Financiamiento (por UE y consolidado Pliego) |
| Bloque 7 | Ejecución por Función a nivel Pliego |
| Bloque 8 | Comparativo histórico (2022–2026, extendido mes a mes) |
| Bloque 9 | Proyección acumulada al 31/12 del año, con vista "Ver Primer Semestre" congelada al 30/06 |

---

## Arquitectura

El dashboard **no depende de ningún backend ni script de conversión**. El parseo de los `.xls` (que en realidad son HTML disfrazado, exportado por Consulta Amigable) ocurre **en vivo, en el navegador**, vía SheetJS embebido en `index.html`.

```
Consulta Amigable MEF (13 archivos .xls)
        ↓
   carpeta xls/ del proyecto
        ↓
  index.html los lee y parsea EN EL NAVEGADOR (SheetJS)
        ↓
  git add / commit / push (manual, vía VS Code)
        ↓
  GitHub Pages publica automáticamente
        ↓
  Tu jefe abre el enlace y ve los datos del día
```

> **Nota histórica:** versiones anteriores de este proyecto usaban un script Python (`convertir_xls_a_json.py`) para pre-procesar los XLS a un `data/ejecucion.json`. Ese enfoque quedó **obsoleto** y fue retirado — el dashboard nunca llegó a depender de ese JSON en su arquitectura actual. No es necesario tener Python instalado para operar el dashboard.

---

## Estructura del Proyecto

```
orad-dashboard/
├── index.html                  ← Dashboard (un solo archivo, autocontenido)
├── actualizar.bat              ← Script de referencia (validación + push automático)
├── data/
│   ├── semestre1_2026.json     ← Snapshot congelado al 30/06/2026 ("Ver Primer Semestre")
│   ├── historico_enejul.json   ← Comparación histórica nacional Ene-Jul (2022-2025)
│   └── rb_hist_sc_enejul.json  ← Comparación histórica Rubro Sede Central Ene-Jul (2022-2025)
├── scripts/
│   └── convertir_semestral.py  ← Genera los JSON congelados de cierre de semestre
├── xls/                        ← Los 13 archivos del día (se suben a Git)
│   └── (ver tabla completa abajo)
└── .gitignore
```

---

## Cómo Actualizar Diariamente

### Paso 1 — Exportar los 13 XLS desde Consulta Amigable

Filtro común a los 13 archivos: **Año = 2026**, **Actividades/Proyectos = "Sólo Proyectos"**, Nivel de Gobierno = R (Regionales) → Sector 99 → Pliego 452.

Consulta Amigable exporta cada archivo con un nombre numérico aleatorio (ej. `64068143.xls`) — **hay que renombrarlo manualmente** al nombre exacto de la tabla siguiente antes de subirlo, porque `index.html` busca cada archivo por su nombre.

| # | Archivo a guardar como | Nivel de drill / Agrupación |
|---|------------------------|------------------------------|
| 1 | `rubro_sede_central.xls` | UE 001-855 (Sede Central) → por Rubro |
| 2 | `rubro_peot.xls` | UE 002-1133 (Proy. Esp. Olmos Tinajones) → por Rubro |
| 3 | `rubro_agricultura.xls` | UE 100-856 (Agricultura) → por Rubro |
| 4 | `rubro_transportes.xls` | UE 200-857 (Transportes) → por Rubro |
| 5 | `rubro_salud.xls` | UE 400-860 (Salud) → por Rubro |
| 6 | `rubro_h_mercedes.xls` | UE 401-1001 (Hospital Las Mercedes) → por Rubro |
| 7 | `rubro_h_belen.xls` | UE 402-1002 (Hospital Belén) → por Rubro |
| 8 | `rubro_h_regional.xls` | UE 403-1422 (Hospital Regional) → por Rubro |
| 9 | `rubro_pliego.xls` | Pliego 452 consolidado (sin UE) → por Rubro |
| 10 | `ue_pliego.xls` | Pliego 452 consolidado → por Unidad Ejecutora |
| 11 | `nacional_gores.xls` | Sector 99 (sin Pliego específico) → por Pliego (26 GOREs) |
| 12 | `funciones_pliego.xls` | Pliego 452 consolidado → por Función |
| 13 | `proyectos_sede_central.xls` | UE 001-855 (Sede Central) → por Proyecto |

> Pegar los 13 en la carpeta `xls/`, reemplazando los del día anterior.

### Paso 2 — Subir a GitHub (vía VS Code)

```bash
git status                 # revisar qué cambió antes de subir nada
git add xls\*.xls          # solo los XLS, nunca "git add ." a ciegas
git commit -m "data: actualización diaria XLS - DD/MM/YYYY"
git push origin main
```

### Paso 3 — Verificar

Esperar 1-2 minutos y abrir `https://jdrq.github.io/orad-dashboard/` (Ctrl+Shift+R para forzar recarga sin caché) y confirmar que los datos del día se reflejan.

---

## Archivos Históricos (comparación Ene–Jul, 2022–2025)

Para extender los bloques de comparación histórica (Bloque 8) se exportan, **una sola vez por mes que cierra**, 8 archivos adicionales por año histórico (4 de ranking nacional + 4 de Rubro Sede Central, formato "mes-solo"). Estos no forman parte de la actualización diaria — se procesan con `scripts/convertir_semestral.py` para generar los JSON de `data/`.

> **Requisito de exportación:** al pedir estos archivos en Consulta Amigable, seleccionar explícitamente la columna de agrupación ("Pliego" o "Rubro") antes de exportar. Si el archivo trae solo una fila "TOTAL", significa que no se seleccionó la agrupación — hay que reexportar.

---

## Modo Manual (sin conexión)

El dashboard funciona igual abriendo `index.html` con doble clic y con los XLS en la carpeta `xls/` local — no requiere servidor ni conexión a internet. El fetch de los JSON de `data/` (históricos y snapshot semestral) es la única parte que depende de estar servido vía GitHub Pages o similar; si falta, el dashboard sigue funcionando con los datos en vivo de los 13 XLS.
