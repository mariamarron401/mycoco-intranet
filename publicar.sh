#!/usr/bin/env bash
#
# publicar.sh — Sincroniza los HTML de trabajo a la intranet, regenera el índice
# y la despliega en Cloudflare Pages (con copia versionada en GitHub).
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

echo "▸ Preparando carpeta de despliegue…"
BUILD="$(mktemp -d)/intranet"
mkdir -p "$BUILD"
cp index.html robots.txt _headers "$BUILD/"
cp -R secciones "$BUILD/"
cp -R assets "$BUILD/"
find "$BUILD" -name '.DS_Store' -delete

echo "▸ Publicando en Cloudflare Pages…"
npx --yes wrangler@4 pages deploy "$BUILD" \
  --project-name mycoco-intranet --branch main --commit-dirty=true
rm -rf "$(dirname "$BUILD")"

echo "▸ Guardando copia en GitHub (control de versiones)…"
git add -A
if git diff --cached --quiet; then
  echo "  (sin cambios que versionar)"
else
  git commit -m "Actualiza intranet ($(date '+%Y-%m-%d %H:%M'))" --quiet
  # Otra sesion puede haber subido cambios: sincronizar antes de publicar.
  git fetch origin main --quiet || true
  if ! git merge -X ours origin/main -m "Merge remoto antes de publicar" --quiet 2>/dev/null; then
    git merge --abort 2>/dev/null || true
    echo "  ⚠ No se pudo fusionar con el remoto; revisa a mano (git status)."
  fi
  git push --quiet || echo "  ⚠ Push a GitHub fallido (la web ya está publicada en Cloudflare)."
fi

echo ""
echo "✓ Publicado. Ya está visible en:"
echo "  https://mycoco-intranet.pages.dev/"
