"""Proveedor de promptfoo: en vez de un LLM, devuelve lo que RECUPERA el RAG (sin costo de API).
config.modo = "semantico" | "hibrido" (hibrido usa vars.termino)."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from comun import recuperar  # noqa: E402


def call_api(prompt, options, context):
    modo = (options.get("config") or {}).get("modo", "semantico")
    termino = context["vars"].get("termino") if modo == "hibrido" else None
    res = recuperar(prompt, k=5, termino=termino)
    salida = [{"archivo": m["archivo"], "pagina": m["pagina"], "sim": round(s, 3)} for _, m, s in res]
    return {"output": json.dumps(salida, ensure_ascii=False)}
