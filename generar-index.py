#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generador de la web MyCoco (intranet + portfolio de marca).

Escanea /secciones/*.html, extrae metadatos (de secciones.json si existen, o del
propio HTML como respaldo) y genera un index.html completo con:
  - Portada (hero) con logo y tagline
  - Manifiesto / misión del movimiento
  - Líneas de actuación
  - Arquitectura de marca (PPR + MyCoco)
  - Portfolio de marca: logos, paleta, tipografías, tono de voz
  - Observatorio de datos (con fuente y fecha en cada cifra)
  - Ecosistema y alianzas
  - Secciones de trabajo (tarjetas auto-generadas desde /secciones)

Ademas garantiza que cada seccion tenga <meta robots noindex> para que la web sea
publica por URL pero NO aparezca en buscadores.

Uso:  python3 generar-index.py   (solo libreria estandar)
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
    with open(ruta, "r", encoding="utf-8", errors="ignore") as f:
        contenido = f.read()
    titulo = None
    m = re.search(r"<title>(.*?)</title>", contenido, re.I | re.S)
    if m:
        titulo = re.sub(r"\s+", " ", m.group(1)).strip()
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
    if re.search(r'name=["\']robots["\']', contenido, re.I):
        return
    nuevo = re.sub(r"(<head[^>]*>)", r"\1\n    " + NOINDEX, contenido, count=1, flags=re.I)
    if nuevo == contenido:
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
    archivos = sorted(f for f in os.listdir(DIR_SECCIONES) if f.lower().endswith(".html"))
    for archivo in archivos:
        ruta = os.path.join(DIR_SECCIONES, archivo)
        t_html, d_html, contenido = extraer_de_html(ruta)
        asegurar_noindex(ruta, contenido)
        m = meta.get(archivo, {})
        fecha_iso = m.get("fecha") or date.fromtimestamp(os.path.getmtime(ruta)).isoformat()
        secciones.append({
            "archivo": archivo,
            "titulo": m.get("titulo") or t_html or archivo,
            "descripcion": m.get("descripcion") or d_html or "",
            "categoria": m.get("categoria") or "General",
            "fecha_iso": fecha_iso,
            "fecha": fecha_legible(fecha_iso),
            "destacado": bool(m.get("destacado")),
        })
    secciones.sort(key=lambda s: s["fecha_iso"], reverse=True)
    secciones.sort(key=lambda s: not s["destacado"])
    return secciones


def color_categoria(cat):
    tabla = {
        "Estrategia": "#3F1910", "Financiación": "#99492C", "Financiacion": "#99492C",
        "Comunidad": "#5B7352", "Marca": "#C6979D", "Observatorio": "#E3A175", "Web": "#5B7352",
    }
    return tabla.get(cat, "#99492C")


def tarjeta(s):
    esc = html.escape
    badge_color = color_categoria(s["categoria"])
    destacado_cls = " tarjeta--destacada" if s["destacado"] else ""
    return f"""        <a class="tarjeta{destacado_cls}" href="secciones/{esc(s['archivo'])}">
          <span class="tarjeta__cat" style="--cat:{badge_color}">{esc(s['categoria'])}</span>
          <h3 class="tarjeta__titulo">{esc(s['titulo'])}</h3>
          <p class="tarjeta__desc">{esc(s['descripcion'])}</p>
          <span class="tarjeta__pie">{esc(s['fecha'])} <span class="tarjeta__flecha">&rarr;</span></span>
        </a>"""


def generar():
    secciones = recopilar()
    n = len(secciones)
    tarjetas = "\n".join(tarjeta(s) for s in secciones) if secciones else \
        '        <p class="vacio">Aún no hay secciones de trabajo publicadas.</p>'
    actualizado = fecha_legible(max((s["fecha_iso"] for s in secciones), default=date.today().isoformat()))

    doc = PLANTILLA.replace("{{TARJETAS}}", tarjetas)
    doc = doc.replace("{{N}}", str(n))
    doc = doc.replace("{{ACTUALIZADO}}", actualizado)
    with open(SALIDA, "w", encoding="utf-8") as f:
        f.write(doc)
    print(f"[OK] index.html generado con {n} sección(es) de trabajo.")


PLANTILLA = r"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  __NOINDEX__
  <title>MyCoco · Movimiento social · Siéntete tú misma</title>
  <meta name="description" content="MyCoco es un movimiento social para que ninguna mujer tenga que decidir sola sobre su cuerpo después de una mastectomía. Marca, estrategia, observatorio de datos y secciones de trabajo.">
  <link rel="icon" href="assets/logo-redondo.png" type="image/png">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Cormorant:ital,wght@0,400;0,500;0,600;0,700;1,400;1,500&family=Poppins:wght@300;400;500;600&display=swap" rel="stylesheet">
  <style>
    :root{
      --beige:#EED8C1; --beige-claro:#F7ECE0; --beige-suave:#FBF5EE;
      --marron:#3F1910; --teja:#99492C; --salmon:#E3A175;
      --rosa:#C6979D; --verde:#5B7352;
      --tinta:#5c4438;
      --sombra:0 8px 30px rgba(63,25,16,.10);
      --sombra-fuerte:0 16px 48px rgba(63,25,16,.18);
      --radio:18px;
      --ancho:1120px;
    }
    *{box-sizing:border-box;margin:0;padding:0}
    html{scroll-behavior:smooth;scroll-padding-top:76px}
    body{
      font-family:'Poppins',system-ui,sans-serif;
      color:var(--marron); background:var(--beige-suave);
      line-height:1.65; -webkit-font-smoothing:antialiased;
    }
    a{color:inherit;text-decoration:none}
    h1,h2,h3,.serif{font-family:'Cormorant',serif}
    .contenedor{max-width:var(--ancho);margin:0 auto;padding:0 24px}
    .eyebrow{
      font-size:.76rem;font-weight:600;letter-spacing:.16em;text-transform:uppercase;
      color:var(--teja);margin-bottom:14px;
    }
    section{padding:88px 0}
    .seccion-h2{
      font-size:clamp(1.9rem,4vw,2.8rem);font-weight:600;line-height:1.1;
      color:var(--marron);margin-bottom:16px;letter-spacing:.3px;
    }
    .seccion-intro{max-width:640px;color:var(--tinta);font-size:1.02rem;margin-bottom:44px}

    /* ---------- NAV ---------- */
    .nav{
      position:sticky;top:0;z-index:50;
      background:rgba(251,245,238,.9);backdrop-filter:blur(10px);
      border-bottom:1px solid rgba(63,25,16,.08);
    }
    .nav__in{
      max-width:var(--ancho);margin:0 auto;padding:12px 24px;
      display:flex;align-items:center;gap:18px;
    }
    .nav__marca{display:flex;align-items:center;gap:10px;font-family:'Cormorant',serif;font-weight:600;font-size:1.3rem}
    .nav__marca img{height:34px;width:34px;border-radius:50%}
    .nav__links{margin-left:auto;display:flex;gap:6px;flex-wrap:wrap}
    .nav__links a{
      font-size:.86rem;font-weight:500;color:var(--tinta);
      padding:8px 14px;border-radius:999px;transition:.15s;
    }
    .nav__links a:hover{background:var(--beige);color:var(--marron)}
    @media (max-width:720px){
      .nav__in{padding:10px 14px;gap:10px}
      .nav__marca{font-size:1.15rem}
      .nav__marca img{height:30px;width:30px}
      /* Menú con scroll horizontal en vez de ocultarse */
      .nav__links{
        margin-left:auto;flex-wrap:nowrap;overflow-x:auto;gap:4px;
        -webkit-overflow-scrolling:touch;scrollbar-width:none;
        max-width:62vw;padding-bottom:2px;
      }
      .nav__links::-webkit-scrollbar{display:none}
      .nav__links a{white-space:nowrap;padding:7px 11px;font-size:.8rem}
    }

    /* ---------- HERO ---------- */
    .hero{
      background:radial-gradient(120% 120% at 50% 0%,var(--beige) 0%,var(--beige-claro) 55%,var(--beige-suave) 100%);
      text-align:center;padding:72px 24px 84px;position:relative;overflow:hidden;
    }
    .hero__logo{height:96px;width:auto;margin-bottom:26px}
    .hero h1{
      font-size:clamp(2.4rem,6vw,4rem);font-weight:600;line-height:1.06;
      max-width:900px;margin:0 auto;letter-spacing:.4px;
    }
    .hero .tagline{
      font-style:italic;font-family:'Cormorant',serif;font-size:1.6rem;
      color:var(--teja);margin-top:10px;
    }
    .hero__frase{
      max-width:680px;margin:26px auto 0;font-size:1.12rem;color:var(--tinta);
    }
    .hero__cta{display:flex;gap:14px;justify-content:center;flex-wrap:wrap;margin-top:34px}
    .btn{
      display:inline-block;padding:13px 26px;border-radius:999px;font-weight:500;
      font-size:.95rem;transition:.18s;border:1.5px solid transparent;
    }
    .btn--primario{background:var(--teja);color:#fff}
    .btn--primario:hover{background:var(--marron);transform:translateY(-2px)}
    .btn--fantasma{border-color:var(--teja);color:var(--teja)}
    .btn--fantasma:hover{background:var(--teja);color:#fff}

    /* ---------- MANIFIESTO ---------- */
    .manifiesto{background:var(--marron);color:var(--beige);text-align:center}
    .manifiesto .cita{
      font-family:'Cormorant',serif;font-size:clamp(1.6rem,4vw,2.5rem);
      font-weight:500;line-height:1.25;max-width:880px;margin:0 auto;
    }
    .manifiesto .cita span{color:var(--salmon)}
    .principios{
      display:grid;gap:18px;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));
      margin-top:48px;text-align:left;
    }
    .principio{
      border:1px solid rgba(238,216,193,.22);border-radius:14px;padding:22px;
      background:rgba(238,216,193,.05);
    }
    .principio strong{font-family:'Cormorant',serif;font-size:1.3rem;color:var(--salmon);display:block;margin-bottom:6px}
    .principio p{font-size:.9rem;color:rgba(238,216,193,.82)}

    /* ---------- TARJETAS genéricas ---------- */
    .grid{display:grid;gap:22px}
    .grid--3{grid-template-columns:repeat(auto-fill,minmax(300px,1fr))}
    .grid--2{grid-template-columns:repeat(auto-fit,minmax(320px,1fr))}
    .card{
      background:#fff;border-radius:var(--radio);padding:26px;
      box-shadow:var(--sombra);border:1px solid rgba(63,25,16,.06);
    }
    .card h3{font-size:1.35rem;font-weight:600;margin-bottom:8px;color:var(--marron)}
    .card p{font-size:.94rem;color:var(--tinta)}

    /* Líneas de actuación */
    .linea{display:flex;gap:16px;align-items:flex-start}
    .linea .num{
      font-family:'Cormorant',serif;font-size:1.8rem;font-weight:600;color:var(--salmon);
      line-height:1;min-width:38px;
    }
    .linea h3{font-size:1.15rem;margin-bottom:2px}
    .linea p{font-size:.88rem}

    /* MVP */
    .mvp{background:var(--beige-claro);border-radius:var(--radio);padding:36px;margin-top:36px}
    .mvp ul{list-style:none;margin-top:14px;display:grid;gap:10px}
    .mvp li{padding-left:26px;position:relative;font-size:.94rem;color:var(--tinta)}
    .mvp li::before{content:"→";position:absolute;left:0;color:var(--teja);font-weight:600}

    /* ---------- ARQUITECTURA MARCA ---------- */
    .duo{display:grid;gap:24px;grid-template-columns:repeat(auto-fit,minmax(300px,1fr))}
    .marca-card{border-radius:var(--radio);padding:32px;box-shadow:var(--sombra)}
    .marca-card--ppr{background:linear-gradient(160deg,#eef1e9,#f6f8f2);border:1px solid rgba(91,115,82,.25)}
    .marca-card--mycoco{background:linear-gradient(160deg,#f8e9dd,#fbf3ec);border:1px solid rgba(198,151,157,.35)}
    .marca-card img{height:44px;margin-bottom:18px}
    .marca-card h3{font-size:1.6rem;margin-bottom:6px}
    .marca-card .rol{font-weight:600;font-size:.8rem;letter-spacing:.1em;text-transform:uppercase;margin-bottom:14px}
    .marca-card--ppr .rol{color:var(--verde)}
    .marca-card--mycoco .rol{color:var(--teja)}
    .marca-card p{font-size:.94rem;color:var(--tinta)}

    /* ---------- PORTFOLIO DE MARCA ---------- */
    .bloque-marca{margin-top:56px}
    .bloque-marca h3.titulo-bloque{
      font-size:1.5rem;font-weight:600;margin-bottom:18px;
      padding-bottom:8px;border-bottom:2px solid var(--beige);
    }
    .logos-grid{display:grid;gap:18px;grid-template-columns:repeat(auto-fill,minmax(180px,1fr))}
    .logo-box{
      border-radius:14px;padding:26px;display:flex;align-items:center;justify-content:center;
      min-height:130px;box-shadow:var(--sombra);
    }
    .logo-box img{max-width:100%;max-height:90px;object-fit:contain}
    .logo-box--claro{background:#fff;border:1px solid rgba(63,25,16,.08)}
    .logo-box--beige{background:var(--beige)}
    .logo-box--oscuro{background:var(--marron)}
    .logo-box--verde{background:#eef1e9;border:1px solid rgba(91,115,82,.2)}
    .logo-cap{font-size:.75rem;color:var(--teja);text-align:center;margin-top:8px;display:block}

    /* Paleta */
    .paleta{display:grid;gap:14px;grid-template-columns:repeat(auto-fill,minmax(150px,1fr))}
    .swatch{border-radius:14px;overflow:hidden;box-shadow:var(--sombra);background:#fff}
    .swatch__color{height:96px}
    .swatch__info{padding:12px 14px}
    .swatch__nombre{font-weight:600;font-size:.9rem}
    .swatch__hex{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.82rem;color:var(--teja)}
    .swatch__uso{font-size:.76rem;color:var(--tinta);margin-top:4px}

    /* Tipografías */
    .tipo{display:grid;gap:22px;grid-template-columns:repeat(auto-fit,minmax(300px,1fr))}
    .tipo-card{background:#fff;border-radius:var(--radio);padding:30px;box-shadow:var(--sombra)}
    .tipo-card .muestra-serif{font-family:'Cormorant',serif;font-size:3.4rem;font-weight:600;line-height:1;color:var(--marron)}
    .tipo-card .muestra-sans{font-family:'Poppins',sans-serif;font-size:2.2rem;font-weight:500;color:var(--marron)}
    .tipo-card .abc{color:var(--tinta);margin-top:12px;font-size:.9rem}
    .tipo-card .rol-tipo{font-size:.8rem;letter-spacing:.1em;text-transform:uppercase;color:var(--teja);font-weight:600;margin-top:16px}

    /* Tono de voz */
    .tono{display:grid;gap:20px;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));margin-top:14px}
    .tono-col{border-radius:var(--radio);padding:26px}
    .tono-col--si{background:#eef3e9;border:1px solid rgba(91,115,82,.3)}
    .tono-col--no{background:#f7e7e2;border:1px solid rgba(153,73,44,.25)}
    .tono-col h4{font-family:'Cormorant',serif;font-size:1.4rem;margin-bottom:12px}
    .tono-col--si h4{color:var(--verde)}
    .tono-col--no h4{color:var(--teja)}
    .tono-col ul{list-style:none;display:grid;gap:8px}
    .tono-col li{font-size:.9rem;padding-left:24px;position:relative;color:var(--tinta)}
    .tono-col--si li::before{content:"✓";position:absolute;left:0;color:var(--verde);font-weight:700}
    .tono-col--no li::before{content:"✕";position:absolute;left:0;color:var(--teja);font-weight:700}

    /* ---------- DATOS / OBSERVATORIO ---------- */
    .datos{background:var(--beige-claro)}
    .stats{display:grid;gap:18px;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));margin-bottom:20px}
    .stat{background:#fff;border-radius:var(--radio);padding:24px;box-shadow:var(--sombra);border-top:4px solid var(--salmon)}
    .stat .cifra{font-family:'Cormorant',serif;font-size:2.6rem;font-weight:700;color:var(--teja);line-height:1}
    .stat .txt{font-size:.86rem;color:var(--tinta);margin-top:6px}
    .stat .fuente{font-size:.72rem;color:var(--rosa);margin-top:10px;font-style:italic}
    .tabla-datos{width:100%;border-collapse:collapse;margin-top:14px;background:#fff;border-radius:var(--radio);overflow:hidden;box-shadow:var(--sombra);font-size:.86rem}
    .tabla-datos th,.tabla-datos td{padding:12px 14px;text-align:left;border-bottom:1px solid rgba(63,25,16,.07)}
    .tabla-datos th{background:var(--marron);color:var(--beige);font-weight:500;font-family:'Poppins'}
    .tabla-datos tr:last-child td{border-bottom:none}
    .tabla-datos td:last-child{color:var(--teja)}
    .scroll-x{overflow-x:auto}
    .vacios{display:grid;gap:10px;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));margin-top:24px}
    .vacio-item{background:#fff;border-radius:12px;padding:16px 18px;box-shadow:var(--sombra);font-size:.9rem;color:var(--tinta);border-left:4px solid var(--rosa)}
    .aviso-datos{margin-top:24px;font-size:.85rem;color:var(--teja);background:rgba(198,151,157,.14);padding:14px 18px;border-radius:12px}

    /* Ecosistema */
    .chips{display:flex;flex-wrap:wrap;gap:10px;margin-top:8px}
    .chip-eco{background:#fff;border:1px solid rgba(63,25,16,.12);border-radius:999px;padding:8px 16px;font-size:.85rem;box-shadow:var(--sombra)}

    /* ---------- SECCIONES DE TRABAJO ---------- */
    .tarjeta{
      background:#fff;border-radius:var(--radio);padding:26px 24px 20px;
      box-shadow:var(--sombra);border:1px solid rgba(63,25,16,.06);
      display:flex;flex-direction:column;gap:10px;position:relative;overflow:hidden;
      transition:transform .18s ease, box-shadow .18s ease;
    }
    .tarjeta::before{content:"";position:absolute;top:0;left:0;right:0;height:4px;
      background:linear-gradient(90deg,var(--teja),var(--salmon),var(--rosa))}
    .tarjeta:hover{transform:translateY(-4px);box-shadow:var(--sombra-fuerte)}
    .tarjeta--destacada{border-color:var(--salmon)}
    .tarjeta__cat{align-self:flex-start;font-size:.7rem;font-weight:600;text-transform:uppercase;
      letter-spacing:.08em;color:#fff;background:var(--cat,#99492C);padding:4px 12px;border-radius:999px}
    .tarjeta__titulo{font-size:1.4rem;font-weight:600;line-height:1.15;color:var(--marron)}
    .tarjeta__desc{font-size:.9rem;color:var(--tinta);flex-grow:1}
    .tarjeta__pie{font-size:.78rem;color:var(--teja);margin-top:6px;display:flex;justify-content:space-between;align-items:center}
    .tarjeta__flecha{font-size:1.1rem;transition:transform .18s ease}
    .tarjeta:hover .tarjeta__flecha{transform:translateX(4px)}
    .vacio{color:var(--teja);font-style:italic;padding:40px 0}
    .contador{display:inline-block;background:var(--beige);color:var(--teja);font-size:.8rem;font-weight:600;padding:5px 14px;border-radius:999px;margin-left:12px;vertical-align:middle}

    /* ---------- FOOTER ---------- */
    footer{background:var(--marron);color:var(--beige);padding:56px 24px 40px;text-align:center}
    footer img{height:40px;margin-bottom:18px;opacity:.95}
    footer .f-tagline{font-family:'Cormorant',serif;font-style:italic;font-size:1.3rem;color:var(--salmon)}
    footer .f-meta{font-size:.85rem;color:rgba(238,216,193,.75);margin-top:14px}
    footer .aviso{max-width:640px;margin:18px auto 0;font-size:.78rem;color:rgba(238,216,193,.6);line-height:1.6}

    /* ---------- MÓVIL (mobile-first refinements) ---------- */
    @media (max-width:600px){
      section{padding:56px 0}
      .contenedor{padding:0 18px}
      .hero{padding:44px 18px 56px}
      .hero__logo{height:70px;margin-bottom:20px}
      .hero__frase{font-size:1rem}
      .hero__cta{flex-direction:column;align-items:stretch}
      .btn{text-align:center}
      .manifiesto .cita{font-size:1.5rem}
      .principios{grid-template-columns:1fr;gap:12px}
      .seccion-intro{margin-bottom:32px}
      .mvp{padding:24px}
      .marca-card,.tipo-card,.card{padding:22px}
      .logos-grid{grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:12px}
      .logo-box{min-height:110px;padding:18px}
      .paleta{grid-template-columns:repeat(2,1fr);gap:10px}
      .stat .cifra{font-size:2.2rem}
      .tipo-card .muestra-serif{font-size:2.6rem}
    }
    @media (max-width:360px){
      .paleta{grid-template-columns:1fr}
      .logos-grid{grid-template-columns:1fr}
    }
  </style>
</head>
<body>

  <!-- NAV -->
  <nav class="nav">
    <div class="nav__in">
      <a class="nav__marca" href="#inicio"><img src="assets/logo-redondo.png" alt="">MyCoco</a>
      <div class="nav__links">
        <a href="#movimiento">El movimiento</a>
        <a href="#arquitectura">Marcas</a>
        <a href="#marca">Identidad</a>
        <a href="#datos">Observatorio</a>
        <a href="#ecosistema">Alianzas</a>
        <a href="#secciones">Secciones</a>
      </div>
    </div>
  </nav>

  <!-- HERO -->
  <header class="hero" id="inicio">
    <img class="hero__logo" src="assets/logos/logo-tagline-horizontal-color.png" alt="MyCoco · Siéntete tú misma">
    <h1>Ninguna mujer debería decidir sola sobre su cuerpo</h1>
    <p class="tagline">Siéntete tú misma</p>
    <p class="hero__frase">MyCoco es un movimiento social, feminista y basado en evidencia que acompaña a mujeres que han vivido o van a vivir una mastectomía. No defendemos una opción sobre otra: defendemos que <strong>todas</strong> sean conocidas, comprendidas, visibles y respetadas.</p>
    <div class="hero__cta">
      <a class="btn btn--primario" href="#secciones">Ver secciones de trabajo</a>
      <a class="btn btn--fantasma" href="#movimiento">Conocer el movimiento</a>
    </div>
  </header>

  <!-- MANIFIESTO -->
  <section class="manifiesto" id="manifiesto">
    <div class="contenedor">
      <p class="cita">MyCoco existe para que ninguna mujer tenga que decidir sola sobre su cuerpo después de una mastectomía. <span>No puede haber decisión informada sin datos, referentes y transparencia.</span></p>
      <div class="principios">
        <div class="principio"><strong>Autonomía corporal</strong><p>La libertad de decidir —reconstruirse, no hacerlo, esperar, prótesis externa o quedarse plana— con igual dignidad para todas las opciones.</p></div>
        <div class="principio"><strong>Rigor y evidencia</strong><p>Cada afirmación de salud, con fuente y fecha. Ni victimismo ni frivolidad: acompañar, no aleccionar.</p></div>
        <div class="principio"><strong>Comunidad</strong><p>Representación, referentes y acompañamiento entre mujeres que han pasado por lo mismo.</p></div>
        <div class="principio"><strong>Datos que faltan</strong><p>Un observatorio que mide lo que España no mide: la calidad de la decisión y la vida tras la mastectomía.</p></div>
      </div>
    </div>
  </section>

  <!-- EL MOVIMIENTO -->
  <section id="movimiento">
    <div class="contenedor">
      <p class="eyebrow">El movimiento</p>
      <h2 class="seccion-h2">Cuerpo + decisión + comunidad + observatorio</h2>
      <p class="seccion-intro">MyCoco acompaña y legitima la libertad de decidir sobre el cuerpo tras una mastectomía, convirtiendo opciones poco visibles en decisiones informadas, acompañadas y socialmente reconocidas. No compite con AECC, FECMA, hospitales ni sociedades científicas: <strong>las complementa</strong>, cubriendo el vacío cultural, comunitario y de datos.</p>

      <h3 class="titulo-bloque" style="font-family:'Cormorant';font-size:1.5rem;margin-bottom:18px">Líneas de actuación</h3>
      <div class="grid grid--3">
        <div class="card"><div class="linea"><span class="num">1</span><div><h3>Alianzas</h3><p>Con empresas comprometidas con la salud femenina, la innovación social y la RSC.</p></div></div></div>
        <div class="card"><div class="linea"><span class="num">2</span><div><h3>Charlas y talleres</h3><p>Mastectomía, reconstrucción, prótesis, sexualidad, autoestima, duelo corporal y toma de decisiones.</p></div></div></div>
        <div class="card"><div class="linea"><span class="num">3</span><div><h3>Red de profesionales</h3><p>Psicología, sexología, fisioterapia, oncología, cirugía, enfermería y acompañamiento.</p></div></div></div>
        <div class="card"><div class="linea"><span class="num">4</span><div><h3>Club de lectura</h3><p>Cáncer, cuerpo, feminismo, autonomía, cicatriz, duelo y reparación.</p></div></div></div>
        <div class="card"><div class="linea"><span class="num">5</span><div><h3>Red de madrinas</h3><p>Mujeres mastectomizadas que acompañan a otras desde la experiencia vivida.</p></div></div></div>
        <div class="card"><div class="linea"><span class="num">6</span><div><h3>Guías y materiales</h3><p>Recursos en lenguaje claro para la toma de decisiones compartida.</p></div></div></div>
        <div class="card"><div class="linea"><span class="num">7</span><div><h3>Observatorio</h3><p>Medición de los vacíos de información sobre la decisión corporal en España.</p></div></div></div>
        <div class="card"><div class="linea"><span class="num">8</span><div><h3>Prótesis externas</h3><p>Como línea de impacto gratuita o subvencionada, no como producto central.</p></div></div></div>
        <div class="card"><div class="linea"><span class="num">9</span><div><h3>Incidencia</h3><p>Llevar la conversación a hospitales, asociaciones, instituciones y gobierno.</p></div></div></div>
      </div>

      <div class="mvp">
        <p class="eyebrow">MVP recomendado — 6 meses</p>
        <h3 style="font-family:'Cormorant';font-size:1.7rem;font-weight:600">Demostrar el problema y la utilidad social, no fabricar producto</h3>
        <ul>
          <li>Guía en lenguaje claro sobre opciones postmastectomía, conectada a AECC, hospitales y sociedades científicas.</li>
          <li>Comunidad piloto con grupos y mentorías (madrinas).</li>
          <li>Micro-observatorio con una primera encuesta nacional.</li>
          <li>Alianzas: al menos 1 hospital + 1 asociación + 1 sociedad científica / unidad de mama.</li>
        </ul>
      </div>
    </div>
  </section>

  <!-- ARQUITECTURA DE MARCA -->
  <section id="arquitectura" style="background:var(--beige-suave)">
    <div class="contenedor">
      <p class="eyebrow">Arquitectura de marca</p>
      <h2 class="seccion-h2">Dos marcas, un ecosistema</h2>
      <p class="seccion-intro">Positivas Pero Realistas da voz y audiencia a MyCoco. En comunicación, PPR es el canal y la comunidad; MyCoco es la causa y el movimiento.</p>
      <div class="duo">
        <div class="marca-card marca-card--ppr">
          <img src="assets/logos/logo-ppr-24.png" alt="Positivas Pero Realistas">
          <p class="rol">Medios y comunidad</p>
          <h3>Positivas Pero Realistas</h3>
          <p>El podcast «donde se habla sin miedo del cáncer de mama». Un espacio seguro y libre de juicios, con tono cercano, humor amable y comunidad. Web: positivasperorealistas.com. Es la audiencia que da altavoz al movimiento.</p>
        </div>
        <div class="marca-card marca-card--mycoco">
          <img src="assets/logos/logo-sencillo-marron.png" alt="MyCoco">
          <p class="rol">El movimiento</p>
          <h3>MyCoco</h3>
          <p>Autonomía corporal, decisión informada, observatorio y acompañamiento. Identidad cálida (marrón, rosa, beige) y voz rigurosa y divulgativa. Web: mycoco.es (en reposicionamiento hacia el relato de movimiento).</p>
        </div>
      </div>
    </div>
  </section>

  <!-- PORTFOLIO DE MARCA -->
  <section id="marca">
    <div class="contenedor">
      <p class="eyebrow">Identidad visual</p>
      <h2 class="seccion-h2">Portfolio de marca</h2>
      <p class="seccion-intro">Logotipos, paleta, tipografías y tono de voz de MyCoco. La identidad completa en un solo lugar para mantener coherencia en todo lo que hacemos.</p>

      <!-- Logos claros -->
      <div class="bloque-marca">
        <h3 class="titulo-bloque">Logotipo principal</h3>
        <div class="logos-grid">
          <div><div class="logo-box logo-box--claro"><img src="assets/logos/logo-completo-horizontal-color.png" alt="Logo completo horizontal color"></div><span class="logo-cap">Completo horizontal</span></div>
          <div><div class="logo-box logo-box--claro"><img src="assets/logos/logo-completo-vertical-color.png" alt="Logo completo vertical color"></div><span class="logo-cap">Completo vertical</span></div>
          <div><div class="logo-box logo-box--claro"><img src="assets/logos/logo-tagline-horizontal-color.png" alt="Logo con tagline"></div><span class="logo-cap">Con tagline</span></div>
          <div><div class="logo-box logo-box--claro"><img src="assets/logos/logo-redondo-color.png" alt="Logo redondo color"></div><span class="logo-cap">Redondo / icono</span></div>
        </div>
      </div>

      <!-- Sobre fondo y símbolo -->
      <div class="bloque-marca">
        <h3 class="titulo-bloque">Versiones sobre fondo y símbolo</h3>
        <div class="logos-grid">
          <div><div class="logo-box logo-box--oscuro"><img src="assets/logos/logo-completo-horizontal-blanco.png" alt="Logo blanco sobre oscuro"></div><span class="logo-cap">Blanco / fondo oscuro</span></div>
          <div><div class="logo-box logo-box--beige"><img src="assets/logos/logo-redondo-beige.png" alt="Logo redondo beige"></div><span class="logo-cap">Beige / fondo cálido</span></div>
          <div><div class="logo-box logo-box--claro"><img src="assets/logos/lazo-color.png" alt="Símbolo lazo color"></div><span class="logo-cap">Símbolo (lazo)</span></div>
          <div><div class="logo-box logo-box--oscuro"><img src="assets/logos/lazo-blanco.png" alt="Símbolo lazo blanco"></div><span class="logo-cap">Símbolo en blanco</span></div>
        </div>
      </div>

      <!-- PPR -->
      <div class="bloque-marca">
        <h3 class="titulo-bloque">Positivas Pero Realistas (medios)</h3>
        <div class="logos-grid">
          <div><div class="logo-box logo-box--verde"><img src="assets/logos/logo-ppr-24.png" alt="Logo PPR"></div><span class="logo-cap">Logo PPR</span></div>
          <div><div class="logo-box logo-box--verde"><img src="assets/logos/logo-redondo-ppr-24.png" alt="Logo redondo PPR"></div><span class="logo-cap">Redondo PPR</span></div>
        </div>
      </div>

      <!-- Paleta -->
      <div class="bloque-marca">
        <h3 class="titulo-bloque">Paleta de color</h3>
        <div class="paleta">
          <div class="swatch"><div class="swatch__color" style="background:#EED8C1"></div><div class="swatch__info"><div class="swatch__nombre">Beige claro</div><div class="swatch__hex">#EED8C1</div><div class="swatch__uso">Fondos cálidos</div></div></div>
          <div class="swatch"><div class="swatch__color" style="background:#3F1910"></div><div class="swatch__info"><div class="swatch__nombre">Marrón oscuro</div><div class="swatch__hex">#3F1910</div><div class="swatch__uso">Texto y títulos</div></div></div>
          <div class="swatch"><div class="swatch__color" style="background:#99492C"></div><div class="swatch__info"><div class="swatch__nombre">Teja / terracota</div><div class="swatch__hex">#99492C</div><div class="swatch__uso">Acentos, botones</div></div></div>
          <div class="swatch"><div class="swatch__color" style="background:#E3A175"></div><div class="swatch__info"><div class="swatch__nombre">Salmón</div><div class="swatch__hex">#E3A175</div><div class="swatch__uso">Destacados cálidos</div></div></div>
          <div class="swatch"><div class="swatch__color" style="background:#C6979D"></div><div class="swatch__info"><div class="swatch__nombre">Rosa malva</div><div class="swatch__hex">#C6979D</div><div class="swatch__uso">Elemento identitario (lazo)</div></div></div>
          <div class="swatch"><div class="swatch__color" style="background:#5B7352"></div><div class="swatch__info"><div class="swatch__nombre">Verde</div><div class="swatch__hex">#5B7352</div><div class="swatch__uso">Nexo con PPR</div></div></div>
        </div>
      </div>

      <!-- Tipografías -->
      <div class="bloque-marca">
        <h3 class="titulo-bloque">Tipografías</h3>
        <div class="tipo">
          <div class="tipo-card">
            <div class="muestra-serif">Cormorant</div>
            <p class="abc">A B C D a b c d — Esto es un título importante</p>
            <p class="rol-tipo">Títulos · serif elegante</p>
          </div>
          <div class="tipo-card">
            <div class="muestra-sans">Poppins</div>
            <p class="abc">A B C D a b c d — Subtítulos y cuerpo de texto</p>
            <p class="rol-tipo">Cuerpo · sans geométrica</p>
          </div>
        </div>
      </div>

      <!-- Tono de voz -->
      <div class="bloque-marca">
        <h3 class="titulo-bloque">Tono de voz</h3>
        <p style="color:var(--tinta);max-width:640px">Humano, joven, feminista, riguroso, inclusivo y basado en evidencia. PPR admite más humor y cercanía; MyCoco mantiene la calidez con más rigor divulgativo.</p>
        <div class="tono">
          <div class="tono-col tono-col--si">
            <h4>Buscamos</h4>
            <ul>
              <li>Autonomía corporal y decisión informada</li>
              <li>Comunidad, representación y acompañamiento</li>
              <li>Rigor con fuente y fecha en cada dato</li>
              <li>Calidez sin idealizar ninguna opción</li>
            </ul>
          </div>
          <div class="tono-col tono-col--no">
            <h4>Evitamos</h4>
            <ul>
              <li>Victimismo y paternalismo</li>
              <li>Tono excesivamente medicalizado</li>
              <li>Romantizar o idealizar una opción corporal</li>
              <li>Afirmaciones de salud sin fuente</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  </section>

  <!-- OBSERVATORIO DE DATOS -->
  <section class="datos" id="datos">
    <div class="contenedor">
      <p class="eyebrow">Observatorio</p>
      <h2 class="seccion-h2">Los datos que faltan</h2>
      <p class="seccion-intro">España mide bien el tumor y razonablemente la supervivencia, pero mide muy mal la autonomía corporal y la calidad de la decisión tras la mastectomía. Ese vacío es la oportunidad de MyCoco. Toda cifra lleva fuente y fecha.</p>

      <div class="stats">
        <div class="stat"><div class="cifra">37.682</div><div class="txt">nuevos casos de cáncer de mama femenino en España (2025)</div><div class="fuente">Fuente: REDECAN, 2025</div></div>
        <div class="stat"><div class="cifra">29%</div><div class="txt">tasa observable de reconstrucción (22% inmediata, 7% diferida)</div><div class="fuente">Estudio SSPA Andalucía, 2010-2013</div></div>
        <div class="stat"><div class="cifra">763 días</div><div class="txt">demora media de la reconstrucción diferida</div><div class="fuente">Estudio SSPA Andalucía</div></div>
        <div class="stat"><div class="cifra">82,3%</div><div class="txt">de profesionales sin formación en decisión compartida</div><div class="fuente">Encuesta oncólogos/cirujanos, Andalucía</div></div>
      </div>

      <div class="scroll-x">
        <table class="tabla-datos">
          <thead><tr><th>Tema</th><th>Situación del dato</th><th>Oportunidad MyCoco</th></tr></thead>
          <tbody>
            <tr><td>Incidencia nacional</td><td>Disponible (REDECAN 2025)</td><td>Traducción ciudadana y territorial</td></tr>
            <tr><td>Reconstrucción inm./diferida</td><td>Parcial (estudio andaluz)</td><td>Registro ciudadano-clínico multicentro</td></tr>
            <tr><td>No reconstrucción / cierre plano</td><td>Muy débil, casi ausente</td><td>Primera medición específica en España</td></tr>
            <tr><td>Prótesis externas</td><td>Uso no medido</td><td>Encuesta de uso, barreras y preferencias</td></tr>
            <tr><td>Decisión compartida</td><td>Evidencia parcial</td><td>Auditoría de la experiencia decisional</td></tr>
            <tr><td>Calidad de vida</td><td>Cada vez mejor descrita (AECC 2025)</td><td>Seguir el impacto por opción corporal</td></tr>
          </tbody>
        </table>
      </div>

      <p class="eyebrow" style="margin-top:36px">Los grandes vacíos</p>
      <div class="vacios">
        <div class="vacio-item">Cuántas mujeres eligen no reconstruirse o quieren cierre plano estético</div>
        <div class="vacio-item">Uso real de prótesis externas: frecuencia, coste y satisfacción</div>
        <div class="vacio-item">% que aplaza la decisión y demora decisional por CCAA</div>
        <div class="vacio-item">Arrepentimiento y satisfacción con la decisión tomada</div>
      </div>

      <p class="aviso-datos"><strong>Fuentes citables:</strong> REDECAN · Estudio reconstrucción SSPA Andalucía · AECC Observatorio e Informe Supervivientes Mama 2025 · Consenso SESPM Salamanca 2024 · AEMPS (protocolo prótesis mamarias 2025) · AEPCIMA. Contenido de salud (YMYL): informativo, nunca consejo médico individual.</p>
    </div>
  </section>

  <!-- ECOSISTEMA -->
  <section id="ecosistema">
    <div class="contenedor">
      <p class="eyebrow">Ecosistema y alianzas</p>
      <h2 class="seccion-h2">No competimos, complementamos</h2>
      <p class="seccion-intro">MyCoco teje alianzas con las entidades que ya trabajan el cáncer de mama en España y con referentes internacionales del cierre plano y la vida tras la mastectomía.</p>
      <div class="grid grid--2">
        <div class="card">
          <h3>Aliados en España</h3>
          <div class="chips">
            <span class="chip-eco">AECC</span><span class="chip-eco">FECMA</span><span class="chip-eco">SESPM</span>
            <span class="chip-eco">SECPRE</span><span class="chip-eco">AEPCIMA</span><span class="chip-eco">Hospitales y unidades de mama</span>
          </div>
        </div>
        <div class="card">
          <h3>Referentes internacionales</h3>
          <div class="chips">
            <span class="chip-eco">Not Putting on a Shirt</span><span class="chip-eco">Flat Friends UK</span>
            <span class="chip-eco">Breast Cancer Now</span><span class="chip-eco">Cancer Research UK</span>
            <span class="chip-eco">Macmillan</span><span class="chip-eco">NHS</span>
          </div>
        </div>
      </div>
    </div>
  </section>

  <!-- SECCIONES DE TRABAJO -->
  <section id="secciones" style="background:var(--beige-suave)">
    <div class="contenedor">
      <p class="eyebrow">Trabajo en curso</p>
      <h2 class="seccion-h2">Secciones de trabajo <span class="contador">{{N}}</span></h2>
      <p class="seccion-intro">Informes, investigaciones y documentos que vamos desarrollando para el movimiento. Comparte esta URL con quien quieras darle acceso. Última actualización: {{ACTUALIZADO}}.</p>
      <div class="grid grid--3">
{{TARJETAS}}
      </div>
    </div>
  </section>

  <!-- FOOTER -->
  <footer>
    <img src="assets/logos/logo-completo-horizontal-blanco.png" alt="MyCoco">
    <p class="f-tagline">Siéntete tú misma</p>
    <p class="f-meta"><strong>MyCoco</strong> — Movimiento social · Sara Gascón Durán</p>
    <p class="aviso">Documento de trabajo interno. Contenido en desarrollo, no destinado a difusión pública. Las cifras de salud recogidas requieren verificación con su fuente antes de cualquier publicación. MyCoco no ofrece consejo médico individual: ante dudas clínicas, consulta con profesionales sanitarios.</p>
  </footer>

</body>
</html>
""".replace("__NOINDEX__", NOINDEX)

if __name__ == "__main__":
    generar()
