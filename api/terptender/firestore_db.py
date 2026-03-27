"""Firestore persistence for TerpTender (dispensaries, products, terpene COAs)."""
from __future__ import annotations

import os
import uuid
from typing import Any, Dict, List, Optional

from google.cloud import firestore
from google.cloud.firestore_v1 import SERVER_TIMESTAMP

PREFIX = os.getenv("TERPTENDER_FIRESTORE_PREFIX", "terptender")


def _coll(name: str) -> str:
    return f"{PREFIX}_{name}"


def _serialize_doc(doc_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(data)
    out["id"] = doc_id
    for key in ("created_at", "updated_at"):
        v = out.get(key)
        if hasattr(v, "isoformat"):
            out[key] = v.isoformat()
    return out


class TerpTenderDB:
    def __init__(self, project_id: Optional[str] = None) -> None:
        pid = project_id or os.getenv("GOOGLE_CLOUD_PROJECT")
        self._db = firestore.Client(project=pid) if pid else firestore.Client()

    # --- Dispensaries ---
    def create_dispensary(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        doc_id = str(uuid.uuid4())
        ref = self._db.collection(_coll("dispensaries")).document(doc_id)
        data = {
            **payload,
            "created_at": SERVER_TIMESTAMP,
            "updated_at": SERVER_TIMESTAMP,
        }
        ref.set(data)
        snap = ref.get()
        return _serialize_doc(doc_id, snap.to_dict() or {})

    def get_dispensary(self, doc_id: str) -> Optional[Dict[str, Any]]:
        ref = self._db.collection(_coll("dispensaries")).document(doc_id)
        snap = ref.get()
        if not snap.exists:
            return None
        return _serialize_doc(doc_id, snap.to_dict() or {})

    def list_dispensaries(self, limit: int = 200) -> List[Dict[str, Any]]:
        q = self._db.collection(_coll("dispensaries")).order_by("name").limit(limit)
        return [_serialize_doc(d.id, d.to_dict() or {}) for d in q.stream()]

    def update_dispensary(self, doc_id: str, patch: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        ref = self._db.collection(_coll("dispensaries")).document(doc_id)
        if not ref.get().exists:
            return None
        clean = {k: v for k, v in patch.items() if v is not None}
        clean["updated_at"] = SERVER_TIMESTAMP
        ref.update(clean)
        snap = ref.get()
        return _serialize_doc(doc_id, snap.to_dict() or {})

    def delete_dispensary(self, doc_id: str) -> bool:
        ref = self._db.collection(_coll("dispensaries")).document(doc_id)
        if not ref.get().exists:
            return False
        ref.delete()
        return True

    # --- Labs (testing partners / LIMS sources) ---
    def create_lab(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        doc_id = str(uuid.uuid4())
        ref = self._db.collection(_coll("labs")).document(doc_id)
        data = {**payload, "created_at": SERVER_TIMESTAMP, "updated_at": SERVER_TIMESTAMP}
        ref.set(data)
        snap = ref.get()
        return _serialize_doc(doc_id, snap.to_dict() or {})

    def get_lab(self, doc_id: str) -> Optional[Dict[str, Any]]:
        ref = self._db.collection(_coll("labs")).document(doc_id)
        snap = ref.get()
        if not snap.exists:
            return None
        return _serialize_doc(doc_id, snap.to_dict() or {})

    def list_labs(self, limit: int = 200) -> List[Dict[str, Any]]:
        q = self._db.collection(_coll("labs")).order_by("name").limit(limit)
        return [_serialize_doc(d.id, d.to_dict() or {}) for d in q.stream()]

    def update_lab(self, doc_id: str, patch: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        ref = self._db.collection(_coll("labs")).document(doc_id)
        if not ref.get().exists:
            return None
        clean = {k: v for k, v in patch.items() if v is not None}
        clean["updated_at"] = SERVER_TIMESTAMP
        ref.update(clean)
        snap = ref.get()
        return _serialize_doc(doc_id, snap.to_dict() or {})

    def delete_lab(self, doc_id: str) -> bool:
        ref = self._db.collection(_coll("labs")).document(doc_id)
        if not ref.get().exists:
            return False
        ref.delete()
        return True

    # --- Products ---
    def create_product(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        doc_id = str(uuid.uuid4())
        ref = self._db.collection(_coll("products")).document(doc_id)
        data = {
            **payload,
            "created_at": SERVER_TIMESTAMP,
            "updated_at": SERVER_TIMESTAMP,
        }
        ref.set(data)
        snap = ref.get()
        return _serialize_doc(doc_id, snap.to_dict() or {})

    def get_product(self, doc_id: str) -> Optional[Dict[str, Any]]:
        ref = self._db.collection(_coll("products")).document(doc_id)
        snap = ref.get()
        if not snap.exists:
            return None
        return _serialize_doc(doc_id, snap.to_dict() or {})

    def list_products(
        self,
        dispensary_id: Optional[str] = None,
        limit: int = 500,
    ) -> List[Dict[str, Any]]:
        col = self._db.collection(_coll("products"))
        if dispensary_id:
            q = col.where("dispensary_id", "==", dispensary_id).limit(limit)
        else:
            q = col.limit(limit)
        return [_serialize_doc(d.id, d.to_dict() or {}) for d in q.stream()]

    def update_product(self, doc_id: str, patch: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        ref = self._db.collection(_coll("products")).document(doc_id)
        if not ref.get().exists:
            return None
        clean = {k: v for k, v in patch.items() if v is not None}
        clean["updated_at"] = SERVER_TIMESTAMP
        ref.update(clean)
        snap = ref.get()
        return _serialize_doc(doc_id, snap.to_dict() or {})

    def delete_product(self, doc_id: str) -> bool:
        ref = self._db.collection(_coll("products")).document(doc_id)
        if not ref.get().exists:
            return False
        ref.delete()
        return True

    # --- COAs ---
    def create_coa(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        doc_id = str(uuid.uuid4())
        ref = self._db.collection(_coll("coas")).document(doc_id)
        data = {
            **payload,
            "created_at": SERVER_TIMESTAMP,
            "updated_at": SERVER_TIMESTAMP,
        }
        ref.set(data)
        snap = ref.get()
        return _serialize_doc(doc_id, snap.to_dict() or {})

    def get_coa(self, doc_id: str) -> Optional[Dict[str, Any]]:
        ref = self._db.collection(_coll("coas")).document(doc_id)
        snap = ref.get()
        if not snap.exists:
            return None
        return _serialize_doc(doc_id, snap.to_dict() or {})

    def list_coas(
        self,
        dispensary_id: Optional[str] = None,
        product_id: Optional[str] = None,
        lab_id: Optional[str] = None,
        limit: int = 500,
    ) -> List[Dict[str, Any]]:
        col = self._db.collection(_coll("coas"))
        if product_id:
            q = col.where("product_id", "==", product_id).limit(limit)
        elif lab_id:
            q = col.where("lab_id", "==", lab_id).limit(limit)
        elif dispensary_id:
            q = col.where("dispensary_id", "==", dispensary_id).limit(limit)
        else:
            q = col.limit(limit)
        return [_serialize_doc(d.id, d.to_dict() or {}) for d in q.stream()]

    def update_coa(self, doc_id: str, patch: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        ref = self._db.collection(_coll("coas")).document(doc_id)
        if not ref.get().exists:
            return None
        clean = {k: v for k, v in patch.items() if v is not None}
        clean["updated_at"] = SERVER_TIMESTAMP
        ref.update(clean)
        snap = ref.get()
        return _serialize_doc(doc_id, snap.to_dict() or {})

    def delete_coa(self, doc_id: str) -> bool:
        ref = self._db.collection(_coll("coas")).document(doc_id)
        if not ref.get().exists:
            return False
        ref.delete()
        return True

    def build_inventory_context(self, dispensary_id: str, max_products: int = 40, max_coas: int = 20) -> str:
        """Compact text for Vertex system context."""
        d = self.get_dispensary(dispensary_id)
        if not d:
            return ""
        lines = [
            f"DISPENSARY: {d.get('name', dispensary_id)} (id={dispensary_id})",
        ]
        if d.get("license_number"):
            lines.append(f"License: {d['license_number']}")
        prods = self.list_products(dispensary_id=dispensary_id, limit=max_products)
        lines.append(f"PRODUCTS ({len(prods)} shown, cap {max_products}):")
        for p in prods:
            lines.append(
                f"  - {p.get('name')} | id={p['id']} | sku={p.get('sku') or '-'} | "
                f"strain={p.get('strain_name') or '-'} | batch={p.get('batch_id') or '-'}"
            )
        coas = self.list_coas(dispensary_id=dispensary_id, limit=max_coas)
        lines.append(f"COAs ({len(coas)} shown, cap {max_coas}):")
        for c in coas:
            ters = c.get("terpenes") or []
            t_summary = ", ".join(
                f"{t.get('name')}:{t.get('percent_wt') or t.get('mg_per_g') or '?'}" for t in ters[:12]
            )
            method = c.get("instrument_method") or ""
            lid = c.get("lab_id") or ""
            lines.append(
                f"  - coa id={c['id']} product_id={c.get('product_id')} lab={c.get('lab_name') or '-'} "
                f"lab_id={lid or '-'} method={method or '-'} "
                f"tested={c.get('tested_at') or '-'} terpenes: {t_summary or 'none listed'}"
            )
        return "\n".join(lines)

    def build_lab_context(self, lab_id: str, max_coas: int = 40) -> str:
        """Context for Vertex: one lab + recent COAs ingested from that lab."""
        lab = self.get_lab(lab_id)
        if not lab:
            return ""
        lines = [
            f"LAB PARTNER: {lab.get('name', lab_id)} (id={lab_id})",
        ]
        if lab.get("license_number"):
            lines.append(f"Lab license: {lab['license_number']}")
        if lab.get("lims_vendor"):
            lines.append(f"LIMS vendor: {lab['lims_vendor']}")
        coas = self.list_coas(lab_id=lab_id, limit=max_coas)
        lines.append(f"COAs from this lab ({len(coas)} shown, cap {max_coas}):")
        for c in coas:
            ters = c.get("terpenes") or []
            t_summary = ", ".join(
                f"{t.get('name')}:{t.get('value')}{t.get('unit') or ''}"
                if t.get("value") is not None
                else f"{t.get('name')}:{t.get('percent_wt') or t.get('mg_per_g') or '?'}"
                for t in ters[:15]
            )
            lines.append(
                f"  - coa={c['id']} dispensary_id={c.get('dispensary_id')} product_id={c.get('product_id')} "
                f"sample={c.get('sample_id') or '-'} batch={c.get('metadata', {}).get('batch_id') or '-'} "
                f"method={c.get('instrument_method') or '-'} terpenes: {t_summary or 'none'}"
            )
        return "\n".join(lines)
