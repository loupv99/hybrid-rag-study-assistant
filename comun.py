"""Piezas compartidas: base Chroma (sin telemetria) y modelo de vectores (cache local)."""
import os
from pathlib import Path

os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")  # Windows sin modo desarrollador: aviso inofensivo
import chromadb
from chromadb.config import Settings
from fastembed import TextEmbedding

RAIZ = Path(__file__).parent
MODELO = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"  # 384 dim, ES+EN


def base():
    return chromadb.PersistentClient(
        path=str(RAIZ / "base_chroma"),
        settings=Settings(anonymized_telemetry=False),
    )


def coleccion(nombre):
    return base().get_or_create_collection(
        nombre, configuration={"hnsw": {"space": "cosine"}}, embedding_function=None
    )


_modelo = None


def vectorizar(textos):
    global _modelo
    if _modelo is None:  # cache dentro del proyecto: el default de fastembed es una carpeta temporal
        _modelo = TextEmbedding(MODELO, cache_dir=str(RAIZ / "modelos"))
    return [v.tolist() for v in _modelo.embed(textos)]


def recuperar(pregunta, k=5, curso=None, termino=None, nombre="maestria"):
    """Top-k trozos como [(texto, metadatos, similitud)].
    Sin `termino`: solo por significado. Con `termino`: hibrido = lista semantica + lista que
    contiene el termino literal, fusionadas por reciprocal rank fusion (1/(60+rango))."""
    col = coleccion(nombre)
    vec = vectorizar([pregunta])
    filtro = {"curso": curso} if curso else None

    def consulta(**extra):
        r = col.query(query_embeddings=vec, n_results=k * 2, where=filtro, **extra)
        return list(zip(r["ids"][0], r["documents"][0], r["metadatas"][0], r["distances"][0]))

    listas = [consulta()]
    if termino:
        listas.append(consulta(where_document={"$contains": termino}))
    puntaje, datos = {}, {}
    for lista in listas:
        for rango, (i, doc, meta, dist) in enumerate(lista):
            puntaje[i] = puntaje.get(i, 0) + 1 / (60 + rango)
            datos[i] = (doc, meta, 1 - dist)
    return [datos[i] for i in sorted(puntaje, key=puntaje.get, reverse=True)[:k]]
