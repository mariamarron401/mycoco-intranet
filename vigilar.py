#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
vigilar.py — Vigilante de la intranet MyCoco.

Observa la(s) carpeta(s) de trabajo y, en cuanto detecta que un HTML se ha
creado O modificado (aunque sea el mismo archivo de siempre), ejecuta
publicar.sh para dejar la intranet SIEMPRE con la última versión.

- Sin dependencias externas (solo librería estándar; sondeo por mtime/tamaño).
- Anti-rebote: espera unos segundos tras el último cambio antes de publicar,
  para no publicar a mitad de guardado ni en cada pulsación.

Uso:
    python3 vigilar.py                 # vigila ../docs
    python3 vigilar.py ../docs ../otra # vigila varias carpetas

Detener: Ctrl+C.
"""

import os
import sys
import time
import subprocess

RAIZ = os.path.dirname(os.path.abspath(__file__))
PUBLICAR = os.path.join(RAIZ, "publicar.sh")

INTERVALO = 2       # segundos entre sondeos
ESPERA_REBOTE = 4   # segundos de calma tras el último cambio antes de publicar


def carpetas_objetivo():
    args = sys.argv[1:]
    if args:
        return [os.path.abspath(a) for a in args]
    return [os.path.abspath(os.path.join(RAIZ, "..", "docs"))]


def firma(carpetas):
    """Huella del estado de todos los .html: {ruta: (mtime, tamaño)}."""
    estado = {}
    for c in carpetas:
        if not os.path.isdir(c):
            continue
        for nombre in os.listdir(c):
            if nombre.lower().endswith(".html"):
                ruta = os.path.join(c, nombre)
                try:
                    st = os.stat(ruta)
                    estado[ruta] = (st.st_mtime, st.st_size)
                except OSError:
                    pass
    return estado


def publicar():
    print("  ▸ Cambios detectados → publicando…", flush=True)
    try:
        subprocess.run(["bash", PUBLICAR], cwd=RAIZ, check=True)
    except subprocess.CalledProcessError as e:
        print(f"  ✗ publicar.sh falló (código {e.returncode}). Reintentaré al próximo cambio.", flush=True)


def diferencias(antes, ahora):
    nuevos = [r for r in ahora if r not in antes]
    modificados = [r for r in ahora if r in antes and ahora[r] != antes[r]]
    borrados = [r for r in antes if r not in ahora]
    return nuevos, modificados, borrados


def main():
    carpetas = carpetas_objetivo()
    print("MyCoco · Vigilante de la intranet")
    print("Vigilando:")
    for c in carpetas:
        marca = "" if os.path.isdir(c) else "  (no existe todavía)"
        print(f"  · {c}{marca}")
    print("Guarda un HTML y se publicará solo. Ctrl+C para detener.\n", flush=True)

    estado = firma(carpetas)
    pendiente_desde = None  # marca temporal del último cambio sin publicar

    try:
        while True:
            time.sleep(INTERVALO)
            actual = firma(carpetas)
            if actual != estado:
                nuevos, modificados, borrados = diferencias(estado, actual)
                for r in nuevos:
                    print(f"  + nuevo: {os.path.basename(r)}", flush=True)
                for r in modificados:
                    print(f"  ~ modificado: {os.path.basename(r)}", flush=True)
                for r in borrados:
                    print(f"  - borrado en origen: {os.path.basename(r)} (se conservará en la intranet)", flush=True)
                estado = actual
                pendiente_desde = time.time()

            # Publicar cuando haya pasado la calma tras el último cambio
            if pendiente_desde is not None and (time.time() - pendiente_desde) >= ESPERA_REBOTE:
                publicar()
                pendiente_desde = None
    except KeyboardInterrupt:
        print("\nVigilante detenido. La intranet queda con lo último publicado.")


if __name__ == "__main__":
    main()
