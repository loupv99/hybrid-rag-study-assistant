"""Resume resultados.json de promptfoo: posicion del acierto y similitud maxima por pregunta."""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
d = json.loads((Path(__file__).parent / "resultados.json").read_text(encoding="utf-8"))
tab = {}
for r in d["results"]["results"]:
    q = r["vars"]["pregunta"][:60]
    out = json.loads(r["response"]["output"])
    tab.setdefault(q, {})[r["provider"]["label"]] = (r["score"], max(x["sim"] for x in out))


def celda(s):
    return ("-" if s[0] == 0 else str(round(1 / s[0]))) + f"/{s[1]:.2f}"


print(f"{'pregunta':60} | semant. pos/sim | hibrido pos/sim")
for q, v in tab.items():
    print(f"{q:60} | {celda(v['semantico']):15} | {celda(v['hibrido'])}")
trampas = {r["vars"]["pregunta"][:60] for r in d["results"]["results"] if not r["vars"].get("esperados")}
for p in ("semantico", "hibrido"):
    sc = [v[p][0] for q, v in tab.items() if q not in trampas]
    print(f"{p:9}: aciertos {sum(s > 0 for s in sc)}/{len(sc)} · en 1.a posicion {sum(s == 1 for s in sc)} · MRR {sum(sc) / len(sc):.3f}")
sims = sorted(v["semantico"][1] for q, v in tab.items() if q not in trampas)
print(f"similitud max. en preguntas CON respuesta: min {sims[0]:.2f}, mediana {sims[len(sims) // 2]:.2f}")
print("similitud max. en TRAMPAS:", ", ".join(f"{v['hibrido'][1]:.2f}" for q, v in tab.items() if q in trampas))
