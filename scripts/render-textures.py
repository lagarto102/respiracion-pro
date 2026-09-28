"""Genera las texturas de papel y tinta de la app (carpeta img/).

Uso (solo hace falta al cambiar las recetas de scripts/ink-recipes.js):
    python scripts/render-textures.py

Ejecuta las recetas SVG de la maqueta en Chromium (Playwright) y guarda el
resultado como imágenes. La app solo pinta mapas de bits: nada de filtros SVG
en tiempo real, que es lo que cuesta en un móvil modesto.

  img/enso-papel.webp    ensō completo en tinta negra (aspecto papel), con transparencia
  img/enso-tinta.webp    el mismo ensō en tinta clara (aspecto tinta)
  img/aguada-papel.webp  aguada de tinta que respira (papel)
  img/aguada-tinta.webp  aguada de tinta que respira (tinta)
  img/papel.webp         baldosa de papel claro (360 px CSS a 2x)
  img/tinta.webp         baldosa de papel oscuro (360 px CSS a 2x)
Los colores de tinta son los de index.html (--ink): #1b1b18 en papel, #ebe3d2 en tinta.
"""
import base64
import pathlib
import sys

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
RECIPES = (ROOT / "scripts" / "ink-recipes.js").read_text(encoding="utf-8")
OUT = ROOT / "img"

PAGE_JS = """
async ({kind, px, look, quality}) => {
  const ink = look === 'tinta' ? '#ebe3d2' : '#1b1b18';
  const load = svg => new Promise((ok, ko) => {
    const img = new Image();
    img.onload = () => ok(img); img.onerror = ko;
    img.src = URL.createObjectURL(new Blob([svg], {type: 'image/svg+xml'}));
  });
  const c = document.createElement('canvas'); c.width = c.height = px;
  const x = c.getContext('2d');
  if (kind === 'enso') {
    x.drawImage(await load(ensoSVG(ink, buildEnso(20260928), px)), 0, 0, px, px);
  } else if (kind === 'aguada') {
    x.drawImage(await load(washSVG(ink, px)), 0, 0, px, px);
  } else {
    // mismo resultado que el ::before con mix-blend-mode de la maqueta, pero ya fundido
    x.fillStyle = look === 'tinta' ? '#1a1b17' : '#f1eadc';
    x.fillRect(0, 0, px, px);
    x.globalCompositeOperation = look === 'tinta' ? 'screen' : 'multiply';
    x.drawImage(await load(grainSVG(look, px)), 0, 0, px, px);
  }
  return c.toDataURL('image/webp', quality);
}
"""

JOBS = [
    ("enso-papel.webp", dict(kind="enso", px=900, look="papel", quality=0.92)),
    ("enso-tinta.webp", dict(kind="enso", px=900, look="tinta", quality=0.92)),
    ("aguada-papel.webp", dict(kind="aguada", px=512, look="papel", quality=0.92)),
    ("aguada-tinta.webp", dict(kind="aguada", px=512, look="tinta", quality=0.92)),
    ("papel.webp", dict(kind="grain", px=720, look="papel", quality=0.9)),
    ("tinta.webp", dict(kind="grain", px=720, look="tinta", quality=0.9)),
]


def main() -> int:
    OUT.mkdir(exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_content("<!doctype html><meta charset=utf-8><body></body>")
        page.add_script_tag(content=RECIPES)
        for name, args in JOBS:
            data_url = page.evaluate(PAGE_JS, args)
            if not data_url.startswith("data:image/webp"):
                print("El navegador no ha devuelto WebP para", name, file=sys.stderr)
                return 1
            raw = base64.b64decode(data_url.split(",", 1)[1])
            (OUT / name).write_bytes(raw)
            print(f"{name}: {len(raw) / 1024:.0f} KB")
        browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
