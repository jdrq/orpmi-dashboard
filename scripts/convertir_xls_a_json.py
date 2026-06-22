#!/usr/bin/env python3
"""
=============================================================================
  CONVERSOR XLS → JSON  |  ORPMI - Gobierno Regional de Lambayeque
  Autor: Juan David Reyes Quintana

  ARCHIVOS QUE PROCESA (12 en total — renombrar tus descargas así):

  Carpeta xls/  ← pegar aquí cada día:
    ue_pliego.xls            Pliego 452 → Por UE → Solo Proyectos
    nacional_gores.xls       Todos GOREs → Por Pliego → Solo Proyectos
    funciones_pliego.xls     Pliego 452 → Por Función → Solo Proyectos
    rubro_pliego.xls         Pliego 452 → Por Rubro → Solo Proyectos
    rubro_sede_central.xls   UE 001-855 → Por Rubro → Solo Proyectos
    rubro_peot.xls           UE 002-1133 → Por Rubro → Solo Proyectos
    rubro_agricultura.xls    UE 100-856 → Por Rubro → Solo Proyectos
    rubro_transportes.xls    UE 200-857 → Por Rubro → Solo Proyectos
    rubro_salud.xls          UE 400-860 → Por Rubro → Solo Proyectos
    rubro_h_mercedes.xls     UE 401-1001 → Por Rubro → Solo Proyectos
    rubro_h_belen.xls        UE 402-1002 → Por Rubro → Solo Proyectos
    rubro_h_regional.xls     UE 403-1422 → Por Rubro → Solo Proyectos

  Carpeta data/historico/  ← cargar UNA SOLA VEZ:
    historico_2016.xls  (mismo formato que ue_pliego.xls pero año 2016)
    historico_2017.xls
    ... hasta historico_2025.xls

  USO:
    Doble clic en actualizar.bat  (Windows)
    — o —
    python scripts/convertir_xls_a_json.py
=============================================================================
"""

import os, re, json, datetime
from pathlib import Path
from bs4 import BeautifulSoup

# ── Rutas ────────────────────────────────────────────────────────────────────
BASE_DIR  = Path(__file__).resolve().parent.parent
XLS_DIR   = BASE_DIR / "xls"
HIST_DIR  = BASE_DIR / "data" / "historico"
OUTPUT    = BASE_DIR / "data" / "ejecucion.json"

# ── Mapa completo de archivos ────────────────────────────────────────────────
ARCHIVOS_PRINCIPALES = {
    "ue_pliego":         XLS_DIR / "ue_pliego.xls",
    "nacional_gores":    XLS_DIR / "nacional_gores.xls",
    "funciones_pliego":  XLS_DIR / "funciones_pliego.xls",
    "rubro_pliego":      XLS_DIR / "rubro_pliego.xls",
}

# Rubros por UE — cada uno alimenta el Bloque 6B (desglose por UE)
ARCHIVOS_RUBRO_UE = {
    "001-855 Sede Central":    XLS_DIR / "rubro_sede_central.xls",
    "002-1133 PEOT":           XLS_DIR / "rubro_peot.xls",
    "100-856 Agricultura":     XLS_DIR / "rubro_agricultura.xls",
    "200-857 Transportes":     XLS_DIR / "rubro_transportes.xls",
    "400-860 Salud":           XLS_DIR / "rubro_salud.xls",
    "401-1001 H. Mercedes":    XLS_DIR / "rubro_h_mercedes.xls",
    "402-1002 H. Belén":       XLS_DIR / "rubro_h_belen.xls",
    "403-1422 H. Regional":    XLS_DIR / "rubro_h_regional.xls",
}

GORE_NOMBRES = {
    "440":"AMAZONAS","441":"ANCASH","442":"APURIMAC","443":"AREQUIPA",
    "444":"AYACUCHO","445":"CAJAMARCA","446":"CALLAO","447":"CUSCO",
    "448":"HUANCAVELICA","449":"HUANUCO","450":"ICA","451":"JUNIN",
    "452":"LAMBAYEQUE","453":"LA LIBERTAD","454":"LORETO","455":"MADRE DE DIOS",
    "456":"MOQUEGUA","457":"PASCO","458":"PIURA","459":"PUNO",
    "460":"SAN MARTIN","461":"TACNA","462":"TUMBES","463":"UCAYALI",
    "464":"LIMA","465":"LIMA PROVINCIAS","999":"MUNI. LIMA"
}

# ── Utilidades ───────────────────────────────────────────────────────────────
def leer(path):
    with open(path, "r", encoding="latin-1") as f:
        return BeautifulSoup(f.read(), "lxml")

def n(txt):
    """'1,234,567' → 1234567.0"""
    try:
        return float(re.sub(r"[,\s]", "", str(txt).strip()))
    except:
        return 0.0

def filas(tabla):
    return [[td.get_text(strip=True) for td in tr.find_all(["td","th"])]
            for tr in tabla.find_all("tr")
            if any(td.get_text(strip=True) for td in tr.find_all(["td","th"]))]

def meta(soup):
    txt = soup.find("table").get_text(" ", strip=True) if soup.find("table") else ""
    fecha = re.search(r"Fecha de la Consulta:\s*([\w\-]+)", txt, re.I)
    anio  = re.search(r"Año de Ejecución:\s*(\d{4})", txt, re.I)
    return {
        "fecha_consulta": fecha.group(1) if fecha else "N/D",
        "anio_ejecucion": int(anio.group(1)) if anio else datetime.date.today().year
    }

def nombre_corto(s):
    parts = str(s).split(":", 1)
    return parts[1].strip() if len(parts) > 1 else s.strip()

# ── Detectar nombre de UE desde contexto ─────────────────────────────────────
def detectar_nombre_ue(soup):
    """Extrae el nombre de la UE del contexto jerárquico (tabla 1)."""
    tables = soup.find_all("table")
    if len(tables) < 2:
        return "Desconocida"
    for row in filas(tables[1]):
        txt = " ".join(row)
        m = re.search(r"Unidad Ejecutora\s+([\w\d\-:, ]+)", txt, re.I)
        if m:
            return m.group(1).strip()
    return "Desconocida"

# ── Parsers ───────────────────────────────────────────────────────────────────
def parsear_ue(path):
    soup   = leer(path)
    tables = soup.find_all("table")
    ues, tot = [], {"pia":0,"pim":0,"cert":0,"comp":0,"dev":0,"girado":0}

    for f in filas(tables[3]):
        if len(f) < 7: continue
        pim = n(f[2]); dev = n(f[6])
        row = dict(
            nombre=f[0], nombre_corto=nombre_corto(f[0]),
            pia=n(f[1]), pim=pim, cert=n(f[3]), comp=n(f[4]),
            dev=dev, girado=n(f[7]) if len(f)>7 else 0,
            avance=n(f[8]) if len(f)>8 else round(dev/pim*100,1) if pim else 0
        )
        for k in ("pia","pim","cert","comp","dev","girado"):
            tot[k] += row[k]
        ues.append(row)

    p = tot["pim"]
    pliego = dict(
        pia=round(tot["pia"]), pim=round(p),
        certificacion=round(tot["cert"]), compromiso=round(tot["comp"]),
        devengado=round(tot["dev"]), girado=round(tot["girado"]),
        por_devengar=round(p-tot["dev"]),
        avance_pct=round(tot["dev"]/p*100,2) if p else 0,
        cert_pct  =round(tot["cert"]/p*100,2) if p else 0,
        comp_pct  =round(tot["comp"]/p*100,2) if p else 0,
    )
    return {"meta": meta(soup), "pliego": pliego, "unidades_ejecutoras": ues}

def parsear_rubro(path):
    soup   = leer(path)
    tables = soup.find_all("table")
    nombre_ue = detectar_nombre_ue(soup)
    rows = []
    for f in filas(tables[3]):
        if len(f) < 7: continue
        pim = n(f[2]); dev = n(f[6])
        rows.append(dict(
            nombre=f[0], nombre_corto=nombre_corto(f[0]),
            nombre_ue=nombre_ue,
            pia=n(f[1]), pim=pim, cert=n(f[3]), comp=n(f[4]),
            dev=dev, girado=n(f[7]) if len(f)>7 else 0,
            avance=n(f[8]) if len(f)>8 else round(dev/pim*100,1) if pim else 0
        ))
    return rows

def parsear_nacional(path):
    soup   = leer(path)
    tables = soup.find_all("table")
    prom   = 38.0
    for f in filas(tables[1]):
        if "GOBIERNOS REGIONALES" in f[0].upper() and len(f) >= 7:
            p = n(f[2]); d = n(f[6])
            if p: prom = round(d/p*100, 1)
            break

    gores = []
    for f in filas(tables[3]):
        if len(f) < 7: continue
        cod = re.match(r"^(\d{3}):", f[0])
        cod = cod.group(1) if cod else "000"
        pim = n(f[2]); dev = n(f[6]); cert = n(f[3])
        av  = n(f[8]) if len(f)>8 else round(dev/pim*100,1) if pim else 0
        gores.append(dict(
            codigo=cod, nombre=f[0],
            nombre_corto=GORE_NOMBRES.get(cod, nombre_corto(f[0])),
            es_lambayeque="452" in f[0],
            pim=pim, cert=cert, dev=dev,
            avance_dev_pct=av,
            avance_cert_pct=round(cert/pim*100,1) if pim else 0,
            sobre_promedio=av >= prom
        ))

    rk_pct  = sorted(gores, key=lambda x: x["avance_dev_pct"], reverse=True)
    rk_sol  = sorted(gores, key=lambda x: x["dev"], reverse=True)
    rk_cert = sorted(gores, key=lambda x: x["avance_cert_pct"], reverse=True)
    for i,g in enumerate(rk_pct):  g["pos_dev_pct"]  = i+1
    for i,g in enumerate(rk_sol):  g["pos_dev_sol"]  = i+1
    for i,g in enumerate(rk_cert): g["pos_cert_pct"] = i+1
    return dict(
        promedio_dev_pct=prom, total_gores=len(gores),
        ranking_dev_pct=rk_pct, ranking_dev_sol=rk_sol, ranking_cert_pct=rk_cert
    )

def parsear_funciones(path):
    soup   = leer(path)
    tables = soup.find_all("table")
    rows = []
    for f in filas(tables[3]):
        if len(f) < 7: continue
        pim = n(f[2]); dev = n(f[6])
        rows.append(dict(
            nombre=f[0], nombre_corto=nombre_corto(f[0]),
            pia=n(f[1]), pim=pim, cert=n(f[3]), comp=n(f[4]),
            dev=dev, por_devengar=round(pim-dev),
            avance=n(f[8]) if len(f)>8 else round(dev/pim*100,1) if pim else 0
        ))
    return rows

def parsear_historico():
    resultado = []
    if not HIST_DIR.exists(): return resultado
    for arch in sorted(HIST_DIR.glob("historico_*.xls")):
        m = re.search(r"historico_(\d{4})\.xls", arch.name, re.I)
        if not m: continue
        anio = int(m.group(1))
        try:
            soup   = leer(arch)
            tables = soup.find_all("table")
            pim_t = dev_t = 0
            for f in filas(tables[3]):
                if len(f) < 7: continue
                pim_t += n(f[2]); dev_t += n(f[6])
            resultado.append(dict(
                anio=anio, pim=round(pim_t), dev=round(dev_t),
                avance=round(dev_t/pim_t*100,1) if pim_t else 0
            ))
            print(f"  ✓ Histórico {anio}: PIM={pim_t:>15,.0f} | Dev={dev_t:>15,.0f}")
        except Exception as e:
            print(f"  ⚠ Error en {arch.name}: {e}")
    return sorted(resultado, key=lambda x: x["anio"])

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print("=" * 62)
    print("  ORPMI — Conversor XLS → JSON")
    print(f"  {datetime.datetime.now().strftime('%d/%m/%Y  %H:%M:%S')}")
    print("=" * 62)

    resultado = {}
    errores   = []
    ok = lambda label: print(f"  ✓ {label}")
    skip = lambda f:   (errores.append(str(f)), print(f"  ✗ No encontrado: {f.name}"))

    # ── 1. UE + KPIs ─────────────────────────────────────────────────────────
    arch = ARCHIVOS_PRINCIPALES["ue_pliego"]
    print(f"\n[1/4] UE del Pliego → {arch.name}")
    if arch.exists():
        d = parsear_ue(arch)
        resultado.update(meta=d["meta"], pliego=d["pliego"],
                         unidades_ejecutoras=d["unidades_ejecutoras"])
        p = d["pliego"]
        ok(f"Pliego PIM={p['pim']:>15,.0f} | Dev={p['devengado']:>15,.0f} | Avance={p['avance_pct']}%")
        ok(f"{len(d['unidades_ejecutoras'])} Unidades Ejecutoras")
    else:
        skip(arch)

    # ── 2. Nacional GOREs ────────────────────────────────────────────────────
    arch = ARCHIVOS_PRINCIPALES["nacional_gores"]
    print(f"\n[2/4] Nacional GOREs → {arch.name}")
    if arch.exists():
        resultado["ranking_nacional"] = parsear_nacional(arch)
        rn = resultado["ranking_nacional"]
        ok(f"{rn['total_gores']} GOREs | Promedio nacional: {rn['promedio_dev_pct']}%")
        lamb = next((g for g in rn["ranking_dev_pct"] if g["es_lambayeque"]), None)
        if lamb:
            ok(f"Lambayeque: puesto {lamb['pos_dev_pct']}°/{rn['total_gores']} | {lamb['avance_dev_pct']}%")
    else:
        skip(arch)

    # ── 3. Funciones ─────────────────────────────────────────────────────────
    arch = ARCHIVOS_PRINCIPALES["funciones_pliego"]
    print(f"\n[3/4] Funciones → {arch.name}")
    if arch.exists():
        resultado["funciones"] = parsear_funciones(arch)
        ok(f"{len(resultado['funciones'])} funciones")
    else:
        skip(arch)

    # ── 4. Rubros ─────────────────────────────────────────────────────────────
    print(f"\n[4/4] Rubros")
    arch = ARCHIVOS_PRINCIPALES["rubro_pliego"]
    print(f"  Pliego completo → {arch.name}")
    if arch.exists():
        resultado["rubros_pliego"] = parsear_rubro(arch)
        ok(f"{len(resultado['rubros_pliego'])} rubros del pliego")
    else:
        skip(arch)

    # Rubros por UE
    rubros_ue = []
    for etiqueta, path in ARCHIVOS_RUBRO_UE.items():
        print(f"  {etiqueta:30s} → {path.name}")
        if path.exists():
            filas_rubro = parsear_rubro(path)
            # Calcular totales de la UE
            pim_ue = sum(r["pim"] for r in filas_rubro)
            dev_ue = sum(r["dev"] for r in filas_rubro)
            rubros_ue.append(dict(
                ue=etiqueta,
                nombre_ue=filas_rubro[0]["nombre_ue"] if filas_rubro else etiqueta,
                rubros=filas_rubro,
                totales=dict(
                    pim=round(pim_ue), dev=round(dev_ue),
                    avance=round(dev_ue/pim_ue*100,1) if pim_ue else 0
                )
            ))
            ok(f"{etiqueta}: {len(filas_rubro)} rubro(s) | PIM={pim_ue:>12,.0f} | Dev={dev_ue:>12,.0f}")
        else:
            print(f"    ✗ No encontrado (opcional)")

    resultado["rubros_por_ue"] = rubros_ue

    # ── Histórico ─────────────────────────────────────────────────────────────
    print(f"\n[+] Histórico → {HIST_DIR}")
    resultado["historico"] = parsear_historico()
    if not resultado["historico"]:
        print("  ℹ Sin archivos históricos (opcional — ver README)")

    # Agregar año en curso al histórico
    if "pliego" in resultado:
        anio_cur = resultado.get("meta", {}).get("anio_ejecucion", datetime.date.today().year)
        resultado["historico"] = [h for h in resultado["historico"] if h["anio"] != anio_cur]
        resultado["historico"].append(dict(
            anio=anio_cur,
            pim=resultado["pliego"]["pim"],
            dev=resultado["pliego"]["devengado"],
            avance=resultado["pliego"]["avance_pct"]
        ))
        resultado["historico"].sort(key=lambda x: x["anio"])

    # ── Guardar ───────────────────────────────────────────────────────────────
    resultado["generado_en"] = datetime.datetime.now().isoformat()
    resultado["errores"]     = errores

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)

    # ── Resumen ───────────────────────────────────────────────────────────────
    print("\n" + "=" * 62)
    tam = OUTPUT.stat().st_size / 1024
    if errores:
        print(f"⚠  COMPLETADO CON {len(errores)} ARCHIVO(S) FALTANTE(S):")
        for e in errores:
            print(f"   • {e}")
    else:
        print("✅  CONVERSIÓN EXITOSA — todos los archivos procesados")
    print(f"📄  JSON: {OUTPUT}  ({tam:.1f} KB)")
    print("=" * 62)
    print("\n🚀  Siguiente paso:")
    print("     git add data/ejecucion.json")
    print("     git commit -m \"Actualización " + datetime.date.today().strftime("%d/%m/%Y") + "\"")
    print("     git push\n")

if __name__ == "__main__":
    main()
