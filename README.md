# Hybrid RAG study assistant

A local retrieval system I built for my MSc in Artificial Intelligence (UNI, Peru). It searches my course
materials by meaning and returns every passage with its source (file and page), so answers can always be
checked. Everything runs on my machine: no API keys, no data leaves the computer.

I use it every day from Claude Code as a tool: the agent calls `buscar.py`, answers only from the retrieved
passages and cites `[file · p. N]`.

## What it does

- **Ingestion** (`ingestar.py`): reads PDF (PyMuPDF), Jupyter notebooks and Markdown. A slide becomes one
  chunk; long pages are split into 1,500-character windows with 200 characters of overlap. Ingestion is
  incremental: a file is re-processed only if its size or modification time changed (re-run with no changes:
  about 4 s).
- **Embeddings** (`comun.py`): `paraphrase-multilingual-MiniLM-L12-v2` through fastembed (384 dimensions,
  Spanish and English), stored in Chroma with cosine distance. Chroma telemetry is turned off.
- **Hybrid retrieval** (`comun.py → recuperar()`): a semantic list plus a list of chunks that contain an exact
  term, merged with reciprocal rank fusion (`1 / (60 + rank)`). The exact list is added, not used as a filter.
- **Search CLI** (`buscar.py`): top k with similarity score, optional course filter.

## Why hybrid: a failure I measured

Semantic search alone returned *Local Response Normalization* (AlexNet) when I asked about *batch
normalization*: similar words, different technique. Adding the exact-term list brought the right section with
its formulas. A first version that **filtered** by the exact term missed it entirely, so the fusion has to
add, not filter.

## Evaluation

Retrieval is evaluated with [promptfoo](https://www.promptfoo.dev/) using a custom Python provider
(`eval/proveedor.py`) that returns what the retriever finds instead of calling an LLM, so an evaluation run
costs nothing. Questions are written **without** the words used in the material, and a hit means one of the
top 5 chunks comes from the expected file. Score = 1 / position of the first hit (MRR).

| Date | Questions | Mode | Hits in top 5 | Hit in 1st place | MRR |
|---|---|---|---|---|---|
| 2026-11-09 | 15 | Semantic | 15/15 | 11 | 0.824 |
| 2026-11-09 | 15 | **Hybrid** | 15/15 | 13 | **0.933** |
| 2026-11-09 (larger corpus) | 18 + 3 traps | Semantic | 18/18 | | 0.781 |
| 2026-11-09 (larger corpus) | 18 + 3 traps | **Hybrid** | 18/18 | 16 | **0.944** |

**What the evaluation taught me.** "Trap" questions are topics verified as absent from the material. With the
first corpus, a similarity threshold of 0.55 separated them from real questions. After adding about 1,800
more chunks (papers and book notebooks), one trap scored 0.61 while real questions started at 0.58: the zones
overlap, so a similarity threshold alone cannot say "this is not in your material". The fix lives in the agent
that uses the tool: a **critic step** that reads the retrieved passages and checks whether they actually
explain the topic or only mention it.

Corpus at that point: 3,467 chunks across four collections (neural networks, big data, an LLM book's
notebooks, and 14 arXiv papers plus technical blog articles).

## Run it

```powershell
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
copy fuentes.example.json fuentes.json      # point each course to a folder with your own PDFs/notebooks
.venv\Scripts\python ingestar.py
.venv\Scripts\python buscar.py "how do residual connections help deep networks"
.venv\Scripts\python buscar.py "batch normalization" --exacto "Batch Normalization"   # hybrid
```

Evaluation (Windows paths in `eval/promptfooconfig.yaml`):

```powershell
cd eval
$env:PROMPTFOO_DISABLE_TELEMETRY="1"
npx -y promptfoo@0.125.1 eval -c promptfooconfig.yaml --no-cache --max-concurrency 1 -o resultados.json
..\.venv\Scripts\python resumen.py
```

`sharing: false` is set in the config so results are never uploaded.

## What is not in this repository

The course PDFs, the vector store and the evaluation outputs are **not** included: they contain text from
copyrighted course materials, books and papers. The test questions in `eval/promptfooconfig.yaml` reference
those files by name, so they reproduce only with the same materials. Bring your own documents and write your
own questions.

## Stack

Python 3.12 · Chroma · fastembed (ONNX) · PyMuPDF · promptfoo · Claude Code (as the agent that calls the tool)

## Author

Lourdes Valeria Pedraza Palomino, Systems Engineer and MSc in AI student.
[LinkedIn](https://www.linkedin.com/in/lou-valeria-pedraza-palomino-ti) · [GitHub](https://github.com/loupv99)

Code: MIT License.
