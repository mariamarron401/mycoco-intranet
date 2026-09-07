# Intranet MyCoco

Sitio web estático (Cloudflare Pages) que reúne las **secciones de trabajo** de MyCoco en HTML.
Cualquier persona con la URL puede consultarlas, sin necesidad de pasarle archivos.

**URL pública:** https://mycoco-intranet.pages.dev/

> Antes estaba en GitHub Pages (`mariamarron401.github.io/mycoco-intranet`). Ese repositorio
> se mantiene como **control de versiones y copia de seguridad**, pero la web que se sirve
> es la de Cloudflare.

> Pública por enlace pero **no indexable** en buscadores (todas las páginas llevan `meta robots noindex`).

## Cómo funciona

- `secciones/` — todos los HTML publicados.
- `assets/` — logo y favicon de MyCoco.
- `index.html` — página de inicio (se **genera automáticamente**, no editar a mano).
- `secciones.json` — metadatos opcionales de cada sección (título, descripción, categoría, fecha, destacado).
- `generar-index.py` — regenera `index.html` y garantiza el `noindex` en cada sección.
- `_headers` — cabeceras de Cloudflare (`X-Robots-Tag: noindex` en todo el sitio).
- `publicar.sh` — sincroniza, regenera, despliega en Cloudflare y versiona en GitHub.

## Publicar cambios

Desde esta carpeta:

```bash
./publicar.sh
```

Esto copia los HTML nuevos de `../docs`, regenera el índice, despliega en Cloudflare Pages
y guarda una copia versionada en GitHub. En Cloudflare los cambios son inmediatos
(unos segundos), no hay que esperar como en GitHub Pages.

Para añadir un HTML que está en otra ruta:

```bash
./publicar.sh ../ruta/al/documento.html
```

## Dar buen título y descripción a una sección

Edita `secciones.json` y añade una entrada con el nombre del archivo. Si no lo haces,
el índice usa el `<title>` del propio HTML y la fecha del archivo.

---
Documento de trabajo interno de MyCoco · Sara Gascón Durán.
