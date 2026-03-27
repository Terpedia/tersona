"""Pydantic models for TerpTender API (dispensaries, products, COAs)."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class Address(BaseModel):
    line1: Optional[str] = None
    line2: Optional[str] = None
    city: Optional[str] = None
    region: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = "US"


class DispensaryCreate(BaseModel):
    name: str = Field(..., min_length=1)
    license_number: Optional[str] = None
    address: Optional[Address] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    notes: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class DispensaryUpdate(BaseModel):
    name: Optional[str] = None
    license_number: Optional[str] = None
    address: Optional[Address] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None


class Dispensary(DispensaryCreate):
    id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ProductCreate(BaseModel):
    dispensary_id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    category: Optional[str] = None
    sku: Optional[str] = None
    strain_name: Optional[str] = None
    batch_id: Optional[str] = None
    brand: Optional[str] = None
    unit: Optional[str] = None
    notes: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    sku: Optional[str] = None
    strain_name: Optional[str] = None
    batch_id: Optional[str] = None
    brand: Optional[str] = None
    unit: Optional[str] = None
    notes: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class Product(ProductCreate):
    id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class TerpeneResult(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str
    percent_wt: Optional[float] = None
    mg_per_g: Optional[float] = Field(None, alias="mg_g")
    relative_percent: Optional[float] = None
    # LIMS-rich fields (structured export / cross-lab harmonization)
    raw_name: Optional[str] = None
    value: Optional[float] = None
    unit: Optional[str] = None
    loq: Optional[float] = None
    lod: Optional[float] = None
    method: Optional[str] = None
    below_loq: Optional[bool] = None


class CannabinoidResult(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str
    percent_wt: Optional[float] = None
    mg_per_g: Optional[float] = Field(None, alias="mg_g")
    raw_name: Optional[str] = None
    value: Optional[float] = None
    unit: Optional[str] = None
    loq: Optional[float] = None
    lod: Optional[float] = None
    method: Optional[str] = None
    below_loq: Optional[bool] = None


class LabCreate(BaseModel):
    name: str = Field(..., min_length=1)
    license_number: Optional[str] = None
    lims_vendor: Optional[str] = None
    contact_email: Optional[str] = None
    website: Optional[str] = None
    notes: Optional[str] = None


class LabUpdate(BaseModel):
    name: Optional[str] = None
    license_number: Optional[str] = None
    lims_vendor: Optional[str] = None
    contact_email: Optional[str] = None
    website: Optional[str] = None
    notes: Optional[str] = None


class Lab(LabCreate):
    id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class LimsAnalyteRow(BaseModel):
    """Single analyte line as labs typically export from LIMS (not only Metrc minimums)."""

    name: str = Field(..., min_length=1)
    value: Optional[float] = None
    unit: Optional[str] = None
    loq: Optional[float] = None
    lod: Optional[float] = None
    method: Optional[str] = None
    below_loq: Optional[bool] = None


class COACreate(BaseModel):
    dispensary_id: str = Field(..., min_length=1)
    product_id: str = Field(..., min_length=1)
    lab_id: Optional[str] = None
    lab_name: Optional[str] = None
    lims_system: Optional[str] = None
    instrument_method: Optional[str] = None
    sample_id: Optional[str] = None
    tested_at: Optional[str] = None
    terpenes: List[TerpeneResult] = Field(default_factory=list)
    cannabinoids: List[CannabinoidResult] = Field(default_factory=list)
    notes: Optional[str] = None
    document_url: Optional[str] = None
    raw_lims: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class COAUpdate(BaseModel):
    lab_id: Optional[str] = None
    lab_name: Optional[str] = None
    lims_system: Optional[str] = None
    instrument_method: Optional[str] = None
    sample_id: Optional[str] = None
    tested_at: Optional[str] = None
    terpenes: Optional[List[TerpeneResult]] = None
    cannabinoids: Optional[List[CannabinoidResult]] = None
    notes: Optional[str] = None
    document_url: Optional[str] = None
    raw_lims: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class COA(COACreate):
    id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ChatMessage(BaseModel):
    role: str
    content: str


class LabResultImport(BaseModel):
    """
    Gold-standard structured payload from a lab LIMS export or API (more than PDF-only COAs).
    Creates a COA row plus normalized terpene/cannabinoid analyte arrays.
    """

    dispensary_id: str = Field(..., min_length=1)
    product_id: str = Field(..., min_length=1)
    lab_id: Optional[str] = None
    lab_name: Optional[str] = None
    lims_system: Optional[str] = None
    sample_id: Optional[str] = None
    batch_id: Optional[str] = None
    product_type: Optional[str] = None
    tested_at: Optional[str] = None
    instrument_method: Optional[str] = None
    terpenes: List[LimsAnalyteRow] = Field(default_factory=list)
    cannabinoids: List[LimsAnalyteRow] = Field(default_factory=list)
    raw_payload: Dict[str, Any] = Field(default_factory=dict)
    document_url: Optional[str] = None
    notes: Optional[str] = None
    normalize: bool = True


class LabResultImportResponse(BaseModel):
    coa: COA
    normalization_log: List[str] = Field(default_factory=list)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    conversation_history: List[ChatMessage] = Field(default_factory=list)
    dispensary_id: Optional[str] = None
    lab_id: Optional[str] = None
    include_inventory_context: bool = True


class ChatResponse(BaseModel):
    response: str
    conversation_history: List[ChatMessage]
