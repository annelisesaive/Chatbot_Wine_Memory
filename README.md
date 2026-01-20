
# Wine_tasting_KG
**Building a wine knowledge graph from large-scale professional reviews to model quality, descriptors, and expertise.**

[![Python](https://img.shields.io/badge/Python-3.x-blue.svg)](#)

## Why this exists
Wine reviews contain high-value information (variety, region, tasting descriptors, quality judgments), but it’s trapped in text. This project converts large-scale review data into a **structured knowledge graph** that supports:
- semantic search (find wines by descriptor profiles)
- similarity and clustering (taste neighborhoods)
- hypothesis testing (e.g., price–rating dynamics, region effects)
- expertise modeling (how language differs with experience)

## What’s inside
- Data preprocessing and normalization (wines, regions, grape varieties, descriptors)
- Graph construction (nodes + edges + attributes)
- Example queries / analyses (similarity, community structure, descriptor hubs)
- Optional: downstream tasks (recommendation, outlier detection)

## Data
The repo is designed to work with a large corpus of professional wine reviews.
If the original dataset cannot be redistributed, include:
- a `data/README.md` explaining required columns and expected formats
- a small synthetic/sample dataset for demo runs (recommended)

## Methods (high-level)
- Text normalization of descriptors (lemmatization / synonym handling where relevant)
- Entity resolution (wine identity across messy strings)
- Graph building (e.g., NetworkX / Neo4j export—depending on your implementation)
- Analytics:
  - centrality (what descriptors/regions dominate)
  - community detection / embeddings
  - predictive baselines (price → rating, etc.) where applicable

## Repository structure
- `data/` – not included / sample only
- `src/` or `scripts/` – ETL + graph build
- `notebooks/` – exploration + figures
- `outputs/` – exported graphs, tables, plots

## Quickstart
```bash
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt

# example build (adjust to your scripts)
python scripts/build_graph.py --input data/reviews.csv --out outputs/wine_kg.graphml
