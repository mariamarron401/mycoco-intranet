#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generador del index de la intranet MyCoco.

Escanea /secciones/*.html, extrae metadatos (de secciones.json si existen, o del
propio HTML como respaldo) y genera un index.html con la marca MyCoco.

Ademas garantiza que cada seccion tenga la etiqueta <meta name="robots" content="noindex...">
para que la intranet sea publica por URL pero NO aparezca en buscadores.

Uso:  python3 generar-index.py
No requiere dependencias externas (solo libreria estandar).
"""

import json
import os
import re
import html
from datetime import datetime, date

RAIZ = os.path.dirname(os.path.abspath(__file__))
DIR_SECCIONES = os.path.join(RAIZ, "secciones")
META_JSON = os.path.join(RAIZ, "secciones.json")
SALIDA = os.path.join(RAIZ, "index.html")

NOINDEX = '<meta name="robots" content="noindex, nofollow">'

MESES = ["", "enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]


def leer_meta():
    if os.path.exists(META_JSON):
        with open(META_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {k: v for k, v in data.items() if not k.startswith("_")}
    return {}


def extraer_de_html(ruta):
    """Titulo (de <title> o primer <h1>) y descripcion (meta description)."""
    with open(ruta, "r", encoding="utf-8", errors="ignore") as f:
        contenido = f.read()
    titulo = None
    m = re.search(r"<title>(.*?)</title>", contenido, re.I | re.S)
    if m:
        titulo = re.sub(r"\s+", " ", m.group(1)).strip()
        # Quitar prefijo "MyCoco ·" para no repetir marca en la tarjeta
        titulo = re.sub(r"^\s*MyCoco\s*[·:\-]\s*", "", titulo, flags=re.I)
    if not titulo:
        m = re.search(r"<h1[^>]*>(.*?)</h1>", contenido, re.I | re.S)
        if m:
            titulo = re.sub(r"<[^>]+>", "", m.group(1))
            titulo = re.sub(r"\s+", " ", titulo).strip()
    desc = None
    m = re.search(r'<meta[^>]+name=["\']description["\'][^>]*content=["\'](.*?)["\']',
                  contenido, re.I | re.S)
    if m:
        desc = re.sub(r"\s+", " ", m.group(1)).strip()
    return titulo, desc, contenido


def asegurar_noindex(ruta, contenido):
    """Inserta la meta noindex en el <head> si no existe. Reescribe el archivo."""
    if re.search(r'name=["\']robots["\']', contenido, re.I):
        return
    nuevo = re.sub(r"(<head[^>]*>)", r"\1\n    " + NOINDEX, contenido, count=1, flags=re.I)
    if nuevo == contenido:  # no habia <head>, no tocamos
        return
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(nuevo)


def fecha_legible(iso):
    try:
        d = datetime.strptime(iso, "%Y-%m-%d").date()
        return f"{d.day} de {MESES[d.month]} de {d.year}"
    except Exception:
        return iso


def recopilar():
    meta = leer_meta()
    secciones = []
    archivos = sorted(
        [f for f in os.listdir(DIR_SECCIONES) if f.lower().endswith(".html")]
    )
    for archivo in archivos:
        ruta = os.path.join(DIR_SECCIONES, archivo)
        t_html, d_html, contenido = extraer_de_html(ruta)
        asegurar_noindex(ruta, contenido)
        m = meta.get(archivo, {})
        fecha_iso = m.get("fecha")
        if not fecha_iso:
            fecha_iso = date.fromtimestamp(os.path.getmtime(ruta)).isoformat()
        secciones.append({
            "archivo": archivo,
            "titulo": m.get("titulo") or t_html or archivo,
            "descripcion": m.get("descripcion") or d_html or "",
            "categoria": m.get("categoria") or "General",
            "fecha_iso": fecha_iso,
            "fecha": fecha_legible(fecha_iso),
            "destacado": bool(m.get("destacado")),
        })
    # Ordenar: destacados primero, luego por fecha descendente
    secciones.sort(key=lambda s: (not s["destacado"], s["fecha_iso"]), reverse=False)
    secciones.sort(key=lambda s: s["fecha_iso"], reverse=True)
    secciones.sort(key=lambda s: not s["destacado"])
    return secciones


def color_categoria(cat):
    tabla = {
        "Estrategia": "#3F1910",
        "Financiación": "#99492C",
        "Financiacion": "#99492C",
        "Comunidad": "#5B7352",
        "Marca": "#C6979D",
        "Observatorio": "#E3A175",
        "Web": "#5B7352",
    }
    return tabla.get(cat, "#99492C")


def tarjeta(s):
    esc = html.escape
    badge_color = color_categoria(s["categoria"])
    destacado_cls = " tarjeta--destacada" if s["destacado"] else ""
    return f"""      <a class="tarjeta{destacado_cls}" href="secciones/{esc(s['archivo'])}">
        <span class="tarjeta__cat" style="--cat:{badge_color}">{esc(s['categoria'])}</span>
        <h2 class="tarjeta__titulo">{esc(s['titulo'])}</h2>
        <p class="tarjeta__desc">{esc(s['descripcion'])}</p>
        <span class="tarjeta__pie">{esc(s['fecha'])} <span class="tarjeta__flecha">→</span></span>
      </a>"""


def generar():
    secciones = recopilar()
    n = len(secciones)
    tarjetas = "\n".join(tarjeta(s) for s in secciones) if secciones else \
        '      <p class="vacio">Aún no hay secciones publicadas.</p>'
    actualizado = fecha_legible(max((s["fecha_iso"] for s in secciones), default=""))

    doc = PLANTILLA.replace("{{TARJETAS}}", tarjetas)
    doc = doc.replace("{{N}}", str(n))
    doc = doc.replace("{{ACTUALIZADO}}", actualizado)
    with open(SALIDA, "w", encoding="utf-8") as f:
        f.write(doc)
    print(f"[OK] index.html generado con {n} sección(es).")


PLANTILLA = """<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  """ + NOINDEX + """
  <title>MyCoco · Intranet de trabajo</title>
  <meta name="description" content="Espacio de trabajo interno de MyCoco: secciones, informes y documentos en desarrollo.">
  <link rel="icon" href="assets/logo-redondo.png" type="image/png">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Cormorant:ital,wght@0,400;0,500;0,600;0,700;1,400&family=Poppins:wght@300;400;500;600&display=swap" rel="stylesheet">
  <style>
    :root{
      --beige:#EED8C1; --marron:#3F1910; --teja:#99492C;
      --salmon:#E3A175; --rosa:#C6979D; --verde:#5B7352;
      --beige-claro:#F7ECE0; --sombra:0 8px 30px rgba(63,25,16,.10);
    }
    *{box-sizing:border-box;margin:0;padding:0}
    body{
      font-family:'Poppins',system-ui,sans-serif;
      color:var(--marron);
      background:var(--beige-claro);
      line-height:1.6;
      -webkit-font-smoothing:antialiased;
    }
    a{color:inherit;text-decoration:none}
    .cabecera{
      background:linear-gradient(160deg,var(--beige) 0%,#F7ECE0 100%);
      border-bottom:1px solid rgba(63,25,16,.08);
      padding:48px 24px 40px;
      text-align:center;
    }
    .cabecera img{height:64px;width:auto;margin-bottom:20px}
    .cabecera h1{
      font-family:'Cormorant',serif;
      font-weight:600;
      font-size:clamp(2rem,5vw,3rem);
      line-height:1.1;
      letter-spacing:.5px;
    }
    .cabecera .tagline{
      font-style:italic;font-family:'Cormorant',serif;
      color:var(--teja);font-size:1.25rem;margin-top:4px;
    }
    .cabecera .lema{
      max-width:640px;margin:18px auto 0;
      font-size:.98rem;color:var(--marron);opacity:.85;
    }
    .meta-barra{
      max-width:1080px;margin:0 auto;padding:20px 24px 0;
      display:flex;flex-wrap:wrap;gap:12px;justify-content:space-between;
      align-items:center;font-size:.85rem;color:var(--teja);
    }
    .meta-barra .chip{
      background:#fff;border:1px solid rgba(63,25,16,.10);
      padding:6px 14px;border-radius:999px;box-shadow:var(--sombra);
    }
    main{max-width:1080px;margin:0 auto;padding:24px 24px 80px}
    .rejilla{
      display:grid;gap:22px;
      grid-template-columns:repeat(auto-fill,minmax(300px,1fr));
      margin-top:20px;
    }
    .tarjeta{
      background:#fff;border-radius:18px;padding:26px 24px 20px;
      box-shadow:var(--sombra);border:1px solid rgba(63,25,16,.06);
      display:flex;flex-direction:column;gap:10px;
      transition:transform .18s ease, box-shadow .18s ease;
      position:relative;overflow:hidden;
    }
    .tarjeta::before{
      content:"";position:absolute;top:0;left:0;right:0;height:4px;
      background:linear-gradient(90deg,var(--teja),var(--salmon),var(--rosa));
    }
    .tarjeta:hover{transform:translateY(-4px);box-shadow:0 14px 40px rgba(63,25,16,.16)}
    .tarjeta--destacada{border-color:var(--salmon)}
    .tarjeta__cat{
      align-self:flex-start;font-size:.72rem;font-weight:600;
      text-transform:uppercase;letter-spacing:.08em;
      color:#fff;background:var(--cat,#99492C);
      padding:4px 12px;border-radius:999px;
    }
    .tarjeta__titulo{
      font-family:'Cormorant',serif;font-weight:600;
      font-size:1.5rem;line-height:1.15;color:var(--marron);
    }
    .tarjeta__desc{font-size:.92rem;color:#5c4438;flex-grow:1}
    .tarjeta__pie{
      font-size:.8rem;color:var(--teja);margin-top:6px;
      display:flex;justify-content:space-between;align-items:center;
    }
    .tarjeta__flecha{font-size:1.1rem;transition:transform .18s ease}
    .tarjeta:hover .tarjeta__flecha{transform:translateX(4px)}
    .vacio{color:var(--teja);font-style:italic;padding:40px 0}
    .seccion-titulo{
      font-family:'Cormorant',serif;font-size:1.6rem;font-weight:600;
      margin-top:8px;
    }
    footer{
      text-align:center;padding:32px 24px 48px;
      font-size:.82rem;color:var(--teja);
      border-top:1px solid rgba(63,25,16,.08);
    }
    footer .aviso{max-width:620px;margin:8px auto 0;opacity:.8}
    @media (max-width:520px){.cabecera{padding:36px 18px 28px}}
  </style>
</head>
<body>
  <header class="cabecera">
    <img src="assets/logo-mycoco.png" alt="MyCoco">
    <h1>Intranet de trabajo</h1>
    <p class="tagline">Siéntete tú misma</p>
    <p class="lema">Espacio interno con las secciones, informes y documentos que vamos desarrollando para el movimiento. Comparte esta URL con quien quieras darle acceso.</p>
  </header>

  <div class="meta-barra">
    <span class="chip">{{N}} sección(es) publicadas</span>
    <span class="chip">Actualizado: {{ACTUALIZADO}}</span>
  </div>

  <main>
    <div class="rejilla">
{{TARJETAS}}
    </div>
  </main>

  <footer>
    <p><strong>MyCoco</strong> — Movimiento social · Origen Corporación Biotech S.L.</p>
    <p class="aviso">Documento de trabajo interno. Contenido en desarrollo, no destinado a difusión pública. Las cifras de salud aquí recogidas requieren verificación con fuente antes de su publicación.</p>
  </footer>
</body>
</html>
"""

if __name__ == "__main__":
    generar()
