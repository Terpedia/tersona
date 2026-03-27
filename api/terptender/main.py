"""
TerpTender — Cloud Run API: Firestore inventory (dispensaries, products, terpene COAs) + Vertex Gemini.
Same GCP project / service-account pattern as gemini-proxy (Tersona).
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Annotated, List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from firestore_db import TerpTenderDB
from models import (
    COA,
    COACreate,
    COAUpdate,
    ChatMessage,
    ChatRequest,
    ChatResponse,
    Dispensary,
    DispensaryCreate,
    DispensaryUpdate,
    Lab,
    LabCreate,
    LabResultImport,
    LabResultImportResponse,
    LabUpdate,
    Product,
    ProductCreate,
    ProductUpdate,
)
from normalization import lims_row_to_cannabinoid_dict, lims_row_to_terpene_dict

GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "terpedia-489015")
GOOGLE_LOCATION = os.getenv("GOOGLE_LOCATION", "us-central1")

VERTEX_INITIALIZED = False

app = FastAPI(title="TerpTender API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://tersona.terpedia.com",
        "https://terpedia.github.io",
        "http://localhost:3000",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_db_singleton: Optional[TerpTenderDB] = None


def get_db() -> TerpTenderDB:
    global _db_singleton
    if _db_singleton is None:
        _db_singleton = TerpTenderDB(GOOGLE_CLOUD_PROJECT)
    return _db_singleton


def init_vertex() -> None:
    global VERTEX_INITIALIZED
    if VERTEX_INITIALIZED:
        return
    try:
        from google.cloud import aiplatform

        aiplatform.init(project=GOOGLE_CLOUD_PROJECT, location=GOOGLE_LOCATION)
        VERTEX_INITIALIZED = True
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Vertex init failed: {e}") from e


Db = Annotated[TerpTenderDB, Depends(get_db)]

_STATIC_DIR = Path(__file__).resolve().parent / "static"


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def terptender_front_page():
    """Product landing: dispensary → COA → labs flywheel (see static/index.html)."""
    index = _STATIC_DIR / "index.html"
    if not index.is_file():
        return HTMLResponse(
            "<h1>TerpTender</h1><p>Landing page missing (static/index.html).</p>",
            status_code=500,
        )
    return HTMLResponse(index.read_text(encoding="utf-8"))


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "terptender",
        "project": GOOGLE_CLOUD_PROJECT,
        "location": GOOGLE_LOCATION,
    }


# --- Dispensaries ---


@app.post("/dispensaries", response_model=Dispensary)
async def create_dispensary(body: DispensaryCreate, db: Db):
    try:
        row = db.create_dispensary(body.model_dump())
        return Dispensary.model_validate(row)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/dispensaries", response_model=List[Dispensary])
async def list_dispensaries(db: Db, limit: int = Query(200, ge=1, le=1000)):
    try:
        rows = db.list_dispensaries(limit=limit)
        return [Dispensary.model_validate(r) for r in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/dispensaries/{dispensary_id}", response_model=Dispensary)
async def get_dispensary(dispensary_id: str, db: Db):
    row = db.get_dispensary(dispensary_id)
    if not row:
        raise HTTPException(status_code=404, detail="Dispensary not found")
    return Dispensary.model_validate(row)


@app.patch("/dispensaries/{dispensary_id}", response_model=Dispensary)
async def patch_dispensary(dispensary_id: str, body: DispensaryUpdate, db: Db):
    patch = body.model_dump(exclude_unset=True)
    row = db.update_dispensary(dispensary_id, patch)
    if not row:
        raise HTTPException(status_code=404, detail="Dispensary not found")
    return Dispensary.model_validate(row)


@app.delete("/dispensaries/{dispensary_id}")
async def delete_dispensary(dispensary_id: str, db: Db):
    if not db.delete_dispensary(dispensary_id):
        raise HTTPException(status_code=404, detail="Dispensary not found")
    return {"ok": True}


# --- Labs (LIMS / testing partners) ---


@app.post("/labs", response_model=Lab)
async def create_lab(body: LabCreate, db: Db):
    try:
        row = db.create_lab(body.model_dump())
        return Lab.model_validate(row)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/labs", response_model=List[Lab])
async def list_labs(db: Db, limit: int = Query(200, ge=1, le=1000)):
    try:
        rows = db.list_labs(limit=limit)
        return [Lab.model_validate(r) for r in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/labs/{lab_id}", response_model=Lab)
async def get_lab(lab_id: str, db: Db):
    row = db.get_lab(lab_id)
    if not row:
        raise HTTPException(status_code=404, detail="Lab not found")
    return Lab.model_validate(row)


@app.patch("/labs/{lab_id}", response_model=Lab)
async def patch_lab(lab_id: str, body: LabUpdate, db: Db):
    patch = body.model_dump(exclude_unset=True)
    row = db.update_lab(lab_id, patch)
    if not row:
        raise HTTPException(status_code=404, detail="Lab not found")
    return Lab.model_validate(row)


@app.delete("/labs/{lab_id}")
async def delete_lab(lab_id: str, db: Db):
    if not db.delete_lab(lab_id):
        raise HTTPException(status_code=404, detail="Lab not found")
    return {"ok": True}


# --- Products ---


@app.post("/products", response_model=Product)
async def create_product(body: ProductCreate, db: Db):
    if not db.get_dispensary(body.dispensary_id):
        raise HTTPException(status_code=400, detail="dispensary_id does not exist")
    try:
        row = db.create_product(body.model_dump())
        return Product.model_validate(row)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/products", response_model=List[Product])
async def list_products(
    db: Db,
    dispensary_id: Optional[str] = None,
    limit: int = Query(500, ge=1, le=2000),
):
    try:
        rows = db.list_products(dispensary_id=dispensary_id, limit=limit)
        return [Product.model_validate(r) for r in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/products/{product_id}", response_model=Product)
async def get_product(product_id: str, db: Db):
    row = db.get_product(product_id)
    if not row:
        raise HTTPException(status_code=404, detail="Product not found")
    return Product.model_validate(row)


@app.patch("/products/{product_id}", response_model=Product)
async def patch_product(product_id: str, body: ProductUpdate, db: Db):
    patch = body.model_dump(exclude_unset=True)
    row = db.update_product(product_id, patch)
    if not row:
        raise HTTPException(status_code=404, detail="Product not found")
    return Product.model_validate(row)


@app.delete("/products/{product_id}")
async def delete_product(product_id: str, db: Db):
    if not db.delete_product(product_id):
        raise HTTPException(status_code=404, detail="Product not found")
    return {"ok": True}


# --- COAs ---


def _coa_payload(body: COACreate) -> dict:
    d = body.model_dump()
    d["terpenes"] = [t.model_dump(by_alias=True) for t in body.terpenes]
    d["cannabinoids"] = [c.model_dump(by_alias=True) for c in body.cannabinoids]
    return d


@app.post("/coas", response_model=COA)
async def create_coa(body: COACreate, db: Db):
    if not db.get_dispensary(body.dispensary_id):
        raise HTTPException(status_code=400, detail="dispensary_id does not exist")
    if not db.get_product(body.product_id):
        raise HTTPException(status_code=400, detail="product_id does not exist")
    if body.lab_id and not db.get_lab(body.lab_id):
        raise HTTPException(status_code=400, detail="lab_id does not exist")
    try:
        row = db.create_coa(_coa_payload(body))
        return COA.model_validate(row)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/coas", response_model=List[COA])
async def list_coas(
    db: Db,
    dispensary_id: Optional[str] = None,
    product_id: Optional[str] = None,
    lab_id: Optional[str] = None,
    limit: int = Query(500, ge=1, le=2000),
):
    try:
        rows = db.list_coas(
            dispensary_id=dispensary_id,
            product_id=product_id,
            lab_id=lab_id,
            limit=limit,
        )
        return [COA.model_validate(r) for r in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/coas/{coa_id}", response_model=COA)
async def get_coa(coa_id: str, db: Db):
    row = db.get_coa(coa_id)
    if not row:
        raise HTTPException(status_code=404, detail="COA not found")
    return COA.model_validate(row)


@app.patch("/coas/{coa_id}", response_model=COA)
async def patch_coa(coa_id: str, body: COAUpdate, db: Db):
    patch = body.model_dump(exclude_unset=True)
    if "terpenes" in patch and body.terpenes is not None:
        patch["terpenes"] = [t.model_dump(by_alias=True) for t in body.terpenes]
    if "cannabinoids" in patch and body.cannabinoids is not None:
        patch["cannabinoids"] = [c.model_dump(by_alias=True) for c in body.cannabinoids]
    if "lab_id" in patch and patch["lab_id"] is not None and not db.get_lab(patch["lab_id"]):
        raise HTTPException(status_code=400, detail="lab_id does not exist")
    row = db.update_coa(coa_id, patch)
    if not row:
        raise HTTPException(status_code=404, detail="COA not found")
    return COA.model_validate(row)


@app.delete("/coas/{coa_id}")
async def delete_coa(coa_id: str, db: Db):
    if not db.delete_coa(coa_id):
        raise HTTPException(status_code=404, detail="COA not found")
    return {"ok": True}


@app.post("/imports/lab-results", response_model=LabResultImportResponse)
async def import_lab_results(body: LabResultImport, db: Db):
    """
    Ingest structured LIMS-style results (analyte name, value, units, LOQ/LOD, method).
    Normalizes terpene naming where enabled; stores raw_payload for audit and PDF backfill workflows.
    """
    if not db.get_dispensary(body.dispensary_id):
        raise HTTPException(status_code=400, detail="dispensary_id does not exist")
    if not db.get_product(body.product_id):
        raise HTTPException(status_code=400, detail="product_id does not exist")
    if body.lab_id and not db.get_lab(body.lab_id):
        raise HTTPException(status_code=400, detail="lab_id does not exist")

    log: List[str] = []
    terpenes: List[dict] = []
    for row in body.terpenes:
        rd = row.model_dump()
        if body.instrument_method and not rd.get("method"):
            rd["method"] = body.instrument_method
        d, notes = lims_row_to_terpene_dict(rd, normalize=body.normalize)
        if d:
            terpenes.append(d)
        log.extend(notes)

    cannabinoids: List[dict] = []
    for row in body.cannabinoids:
        rd = row.model_dump()
        if body.instrument_method and not rd.get("method"):
            rd["method"] = body.instrument_method
        d, notes = lims_row_to_cannabinoid_dict(rd, normalize=body.normalize)
        if d:
            cannabinoids.append(d)
        log.extend(notes)

    lab_name = body.lab_name
    if body.lab_id and not lab_name:
        lab_row = db.get_lab(body.lab_id)
        if lab_row:
            lab_name = lab_row.get("name")

    meta: dict = {}
    if body.batch_id:
        meta["batch_id"] = body.batch_id
    if body.product_type:
        meta["product_type"] = body.product_type

    coa_payload = {
        "dispensary_id": body.dispensary_id,
        "product_id": body.product_id,
        "lab_id": body.lab_id,
        "lab_name": lab_name,
        "lims_system": body.lims_system,
        "instrument_method": body.instrument_method,
        "sample_id": body.sample_id,
        "tested_at": body.tested_at,
        "terpenes": terpenes,
        "cannabinoids": cannabinoids,
        "notes": body.notes,
        "document_url": body.document_url,
        "raw_lims": body.raw_payload,
        "metadata": meta,
    }
    try:
        row = db.create_coa(coa_payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    return LabResultImportResponse(coa=COA.model_validate(row), normalization_log=log)


# --- Vertex chat (inventory-aware) ---

TERPTENDER_SYSTEM = """You are TerpTender, an assistant for licensed cannabis retail and lab data partnerships.
You help staff interpret inventory, products, and lab COAs — especially full terpene panels, units, LOQ/LOD, and method context
that often never appear in compliance-only systems. You may also reason about data from testing labs as a neutral partner
(not replacing Metrc or lab LIMS). Be accurate: if data is not in the provided context, say you do not have it.
Use plain language. Do not give medical claims or dosing advice.
Respond in plain text only (no markdown)."""


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, db: Db):
    init_vertex()
    try:
        from vertexai.generative_models import GenerativeModel
    except ImportError as e:
        raise HTTPException(status_code=503, detail=f"Vertex SDK missing: {e}") from e

    parts: List[str] = []
    if req.dispensary_id and req.include_inventory_context:
        block = db.build_inventory_context(req.dispensary_id)
        if not block:
            raise HTTPException(status_code=404, detail="dispensary_id not found")
        parts.append(block)
    if req.lab_id and req.include_inventory_context:
        block = db.build_lab_context(req.lab_id)
        if not block:
            raise HTTPException(status_code=404, detail="lab_id not found")
        parts.append(block)

    system = TERPTENDER_SYSTEM
    if parts:
        system += "\n\nCURRENT DATA (authoritative for this session):\n" + "\n\n---\n\n".join(parts)

    model = GenerativeModel(
        model_name=os.getenv("TERPTENDER_MODEL", "gemini-2.0-flash-001"),
        system_instruction=system,
    )

    lines: List[str] = []
    for m in req.conversation_history:
        role, content = m.role, m.content
        if role == "user":
            lines.append(f"User: {content}")
        else:
            lines.append(f"Assistant: {content}")
    lines.append(f"User: {req.message}")
    prompt = "\n".join(lines)

    try:
        resp = model.generate_content(prompt)
        text = (resp.text or "").strip() if resp else ""
        if not text:
            raise ValueError("Empty model response")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {e}") from e

    hist = list(req.conversation_history)
    hist.append(ChatMessage(role="user", content=req.message))
    hist.append(ChatMessage(role="assistant", content=text))
    return ChatResponse(response=text, conversation_history=hist)
