#!/usr/bin/env bash
#
# publicar.sh — Sincroniza los HTML de trabajo a la intranet, regenera el índice
# y lo sube a GitHub Pages.
#
# Uso:
#   ./publicar.sh                          # sincroniza desde las carpetas FUENTE y publica
#   ./publicar.sh ruta/a/nuevo.html ...    # además copia esos HTML concretos a /secciones
#
set -euo pipefail
cd "$(dirname "$0")"

# Carpetas del proyecto donde solemos crear HTML. Añade más si hace falta.
FUENTES=("../docs")

echo "▸ Sincronizando secciones…"
for dir in "${FUENTES[@]}"; do
  if [ -d "$dir" ]; then
    shopt -s nullglob
    for f in "$dir"/*.html; do
      cp -v "$f" "secciones/"
    done
    shopt -u nullglob
  fi
done

# HTML sueltos pasados como argumentos
for f in "$@"; do
  if [ -f "$f" ]; then
    cp -v "$f" "secciones/"
  fi
done

echo "▸ Regenerando index.html (con marca + noindex)…"
python3 generar-index.py

echo "▸ Publicando en GitHub…"
git add -A
if git diff --cached --quiet; then
  echo "  (sin cambios que publicar)"
else
  MSG="Actualiza intranet ($(date '+%Y-%m-%d %H:%M'))"
  git commit -m "$MSG"
  # Otra sesión puede haber subido cambios: sincronizar antes de publicar.
  # -X ours conserva los archivos nuevos del remoto y solo resuelve los
  # conflictos de contenido a favor de nuestra versión (contenido + barra + noindex).
  git fetch origin main --quiet || true
  if ! git merge -X ours origin/main -m "Merge remoto antes de publicar" --quiet 2>/dev/null; then
    git merge --abort 2>/dev/null || true
    echo "  ⚠ No se pudo fusionar automáticamente con el remoto; revisa a mano (git status)."
  fi
  git push
  echo "✓ Publicado. En 1-2 min estará visible en:"
  echo "  https://mariamarron401.github.io/mycoco-intranet/"
fi
