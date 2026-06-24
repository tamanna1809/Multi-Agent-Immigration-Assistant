import json
import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from state import ImmigrationState, RiskAssessment
from tools.rag_tool import search_immigration_rules
from tools.search_tool import search_current_processing_times

llm = ChatOpenAI(
    model="gpt-4o",
    base_url="https://models.inference.ai.azure.com",
    api_key=os.environ["GITHUB_TOKEN"],
    temperature=0,
)


def risk_agent(state: ImmigrationState) -> dict:
    """Agent 4: Assesses application risk using RAG + live web search. Estimates timeline and approval probability."""
    profile = state["user_profile"]
    visa_type = state["visa_recommendation"]["visa_type"]
    missing_docs = state["document_checklist"].get("missing_count", 0)

    # Tool 1: RAG — get risk factors from knowledge base
    risk_rules = search_immigration_rules.invoke(
        f"{visa_type} risk factors rejection red flags common reasons"
    )

    # Tool 2: Web Search — get current processing times
    current_times = search_current_processing_times.invoke(
        f"{visa_type} visa processing time 2025 USCIS IRCC"
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a senior immigration risk analyst.

Analyze the applicant's profile, missing documents, and known risk factors to produce
an honest, specific risk assessment.

Be direct about risks. Do not be overly optimistic.

Risk Level Guidelines:
- "low": Strong profile, no red flags, all documents likely obtainable, >80% approval likely
- "medium": Some concerns but manageable, 50-80% approval likely
- "high": Significant red flags (prior rejection, criminal record, weak ties), <50% approval likely

Knowledge Base — Risk Factors:
{risk_rules}

Current Processing Times (from web):
{current_times}"""),
        ("human", """Visa Type: {visa_type}
Applicant Profile: {profile}
Missing Documents (count): {missing_docs}

Document Analysis Results:
- Document Quality Score: {doc_score}/100
- Critical Document Issues: {doc_issues}
- Verified Documents: {docs_verified}
- Still Missing Documents: {docs_missing}

Use the document analysis results to give a more accurate approval probability.
If document score is low or there are critical issues, reflect that in the risk level.""")
    ])

    # Document analysis results (if available)
    doc_analysis = state.get("document_analysis") or {}
    doc_score = doc_analysis.get("overall_document_score", "N/A")
    doc_issues = doc_analysis.get("critical_issues", [])
    docs_verified = doc_analysis.get("documents_verified", [])
    docs_missing = doc_analysis.get("documents_still_missing", [])

    structured_llm = llm.with_structured_output(RiskAssessment, method="function_calling")
    result = (prompt | structured_llm).invoke({
        "risk_rules": risk_rules,
        "current_times": current_times,
        "visa_type": visa_type,
        "profile": json.dumps(profile, indent=2),
        "missing_docs": missing_docs,
        "doc_score": doc_score,
        "doc_issues": json.dumps(doc_issues),
        "docs_verified": json.dumps(docs_verified),
        "docs_missing": json.dumps(docs_missing),
    })

    return {
        "risk_assessment": result.model_dump(),
        "messages": [{
            "role": "risk_agent",
            "content": (
                f"Risk Assessment: {result.overall_risk_level.upper()} | "
                f"Approval probability: {result.approval_probability_pct}% | "
                f"Processing: {result.estimated_processing_days_min}–{result.estimated_processing_days_max} days | "
                f"{len(result.risk_factors)} risk factors identified"
            )
        }]
    }
