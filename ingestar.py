"""Carga PDFs y notebooks en Chroma. Incremental: solo reprocesa archivos nuevos o modificados.

Uso:  .venv\\Scripts\\python ingestar.py [coleccion]      (por defecto: todas las de fuentes.json)
"""
import hashlib
import json
import sys
from pathlib import Path

import pymupdf as fitz

from comun import RAIZ, coleccion, vectorizar

TAM, SOLAPE = 1500, 200  # caracteres por trozo / solapamiento entre trozos


def trozos(texto):
    """Pagina corta (diapositiva) = 1 trozo. Pagina larga (paper) = ventanas de TAM con SOLAPE."""
    texto = " ".join(texto.split())
    if len(texto) <= TAM + 300:
        return [texto] if len(texto) >= 40 else []
    out, i = [], 0
    while i < len(texto):
        out.append(texto[i : i + TAM])
        i += TAM - SOLAPE
    return out


def unidades(ruta):
    """(numero_de_pagina_o_celda, texto) por archivo."""
    if ruta.suffix.lower() == ".pdf":
        with fitz.open(ruta) as doc:
            return [(n + 1, pg.get_text("text")) for n, pg in enumerate(doc)]
    if ruta.suffix.lower() == ".ipynb":
        celdas = json.loads(ruta.read_text(encoding="utf-8")).get("cells", [])
        return [(n + 1, "".join(c.get("source", []))) for n, c in enumerate(celdas)]
    if ruta.suffix.lower() == ".md":  # articulos en Markdown: 1 unidad por seccion '## '
        crudo = ruta.read_bytes()  # algunos .md vienen en UTF-16 (BOM FF FE)
        texto = crudo.decode("utf-16") if crudo[:2] in (b"\xff\xfe", b"\xfe\xff") else crudo.decode("utf-8", "replace")
        secciones = texto.split("\n## ")
        return [(n + 1, s) for n, s in enumerate(secciones)]
    return []


def ingestar(nombre, fuente):
    col = coleccion(nombre)
    nuevos = saltados = 0
    for curso, carpeta in fuente["carpetas"].items():
        for ruta in sorted(Path(carpeta).rglob("*")):  # incluye subcarpetas (p. ej. chapterNN/ del libro)
            if (ruta.suffix.lower() not in (".pdf", ".ipynb", ".md") or ruta.name.lower() == "readme.md"
                    or any(p.startswith(".") for p in ruta.relative_to(carpeta).parts)):  # .git, .setup...
                continue
            firma = f"{ruta.stat().st_size}-{int(ruta.stat().st_mtime)}"
            previo = col.get(where={"ruta": str(ruta)}, limit=1, include=["metadatas"])
            if previo["ids"] and previo["metadatas"][0].get("firma") == firma:
                saltados += 1
                continue
            col.delete(where={"ruta": str(ruta)})  # archivo modificado: se rehace entero
            ids, docs, metas = [], [], []
            for pag, texto in unidades(ruta):
                for k, t in enumerate(trozos(texto)):
                    ids.append(hashlib.sha1(f"{ruta}|{pag}|{k}".encode()).hexdigest())
                    docs.append(t)
                    metas.append({"curso": curso, "archivo": ruta.name, "pagina": pag,
                                  "tipo": ruta.suffix.lower()[1:], "ruta": str(ruta), "firma": firma})
            for i in range(0, len(ids), 64):
                col.add(ids=ids[i:i + 64], documents=docs[i:i + 64],
                        metadatas=metas[i:i + 64], embeddings=vectorizar(docs[i:i + 64]))
            nuevos += 1
            print(f"  + {curso}/{ruta.name}: {len(ids)} trozos")
    print(f"[{nombre}] {nuevos} archivos cargados, {saltados} sin cambios, {col.count()} trozos en total")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    fuentes = json.loads((RAIZ / "fuentes.json").read_text(encoding="utf-8"))
    for nombre in sys.argv[1:] or fuentes:
        ingestar(nombre, fuentes[nombre])
