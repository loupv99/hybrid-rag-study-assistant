"""Busca los trozos mas relevantes y los imprime con su fuente (archivo + pagina).

Uso:
  .venv\\Scripts\\python buscar.py "que es batch normalization"
  .venv\\Scripts\\python buscar.py "spark mllib" --curso big-data -k 3
  .venv\\Scripts\\python buscar.py "normalizacion por lotes" --exacto "Batch Normalization"   (hibrido)
"""
import argparse
import sys

from comun import recuperar

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
p = argparse.ArgumentParser()
p.add_argument("pregunta")
p.add_argument("--coleccion", default="maestria")
p.add_argument("--curso")
p.add_argument("--exacto", help="hibrido: suma los trozos que contienen este texto literal")
p.add_argument("-k", type=int, default=5)
a = p.parse_args()

res = recuperar(a.pregunta, a.k, a.curso, a.exacto, a.coleccion)
if not res:
    print("Sin resultados.")
for n, (doc, meta, sim) in enumerate(res, 1):
    lugar = {"ipynb": "celda", "md": "secc."}.get(meta["tipo"], "p.")
    print(f"\n[{n}] {meta['curso']} · {meta['archivo']} · {lugar} {meta['pagina']}  (similitud {sim:.2f})")
    print(doc[:1200])
