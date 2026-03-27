# Terpene COA knowledge base (by strain)

Versioned, **human-curated** JSON records that tie **terpene (and optional cannabinoid) COA-style data** to **cannabis strains**. Use this for documentation, RAG, comparisons, and seeding UX—not as a substitute for **lab-issued COAs** for compliance.

## Layout

| Path | Purpose |
|------|---------|
| `schema/strain-coa.schema.json` | JSON Schema for strain files |
| `strains/*.json` | One file per strain (`strain_id` = basename) |
| `strains/_template.json` | Copy to add a new strain |
| `index.json` | Discoverable list of strains (update when adding files) |

## Relationship to TerpTender

- **`kb/`** — static, reviewable “reference” shapes (strain → one or more `coa_entries` with provenance).
- **`api/terptender/`** — operational DB (Firestore) for dispensaries, products, and **real** structured LIMS ingests (`POST /imports/lab-results`).

Workflow: verified lab rows can be summarized into `kb/strains/…` with `source_type: "single_lab_coa"` and a **citation**, or you can keep authoritative numbers only in TerpTender and use `kb` for aliases + narrative.

## Provenance (`source_type`)

Use `single_lab_coa` only when you can cite lab + sample/batch. Prefer `market_aggregate`, `literature`, or `placeholder` until then. Every aggregate entry should carry a **disclaimer** in the JSON.

## Adding a strain

1. Copy `strains/_template.json` → `strains/<strain-id>.json` (kebab-case `strain_id`).
2. Fill `coa_entries[].terpenes[]` with `analyte`, optional `value` + `unit`, optional `canonical` (align with `api/terptender/normalization.py` slugs when possible).
3. Append an object to `index.json` → `strains`.

Optional: validate with any JSON Schema CLI against `schema/strain-coa.schema.json`.
