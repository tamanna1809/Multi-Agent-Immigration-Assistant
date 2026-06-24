from typing import TypedDict, Optional, List, Annotated
from pydantic import BaseModel
import operator


class VisaRecommendation(BaseModel):
    visa_type: str
    visa_name: str
    confidence_score: float
    reasoning: str
    alternative_visas: List[str] = []


class DocumentItem(BaseModel):
    name: str
    required: bool
    status: str = "missing"
    notes: Optional[str] = None


class DocumentChecklist(BaseModel):
    visa_type: str
    documents: List[DocumentItem]
    missing_count: int
    ready_to_proceed: bool


class FormField(BaseModel):
    field_id: str
    label: str
    value: Optional[str] = None
    auto_filled: bool = False
    needs_review: bool = False
    review_reason: Optional[str] = None


class FilledForm(BaseModel):
    form_name: str
    form_id: str
    fields: List[FormField]
    completion_percentage: float
    flagged_fields: List[str]


class AnalyzedDocument(BaseModel):
    file_path: str
    document_type: str        # "passport", "degree", "offer_letter", etc.
    extracted_info: List[str] # key fields as "field: value" strings e.g. ["Name: Arjun", "Expiry: 2032"]
    issues: List[str]         # problems found (expired, wrong field, missing signature)
    validity_status: str      # "valid", "expired", "incomplete", "unreadable"
    relevance_to_visa: str    # how relevant this doc is


class DocumentAnalysisResult(BaseModel):
    analyzed_documents: List[AnalyzedDocument]
    overall_document_score: int   # 0-100
    critical_issues: List[str]
    documents_verified: List[str]
    documents_still_missing: List[str]
    summary: str


class RiskFactor(BaseModel):
    category: str
    description: str
    severity: str
    mitigation_advice: str


class RiskAssessment(BaseModel):
    overall_risk_level: str
    approval_probability_pct: int
    estimated_processing_days_min: int
    estimated_processing_days_max: int
    risk_factors: List[RiskFactor]
    final_recommendation: str


class ImmigrationState(TypedDict):
    user_profile: dict
    visa_recommendation: Optional[dict]
    document_checklist: Optional[dict]
    document_analysis: Optional[dict]    # NEW: results from analyzing uploaded docs
    filled_form: Optional[dict]
    risk_assessment: Optional[dict]
    human_decision: Optional[str]
    human_feedback: Optional[str]
    needs_clarification: bool
    clarification_questions: List[str]
    messages: Annotated[List[dict], operator.add]
    errors: List[str]
    final_report: Optional[str]
