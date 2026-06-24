import os
import json
from pathlib import Path
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from state import ImmigrationState, DocumentAnalysisResult

llm = ChatOpenAI(
    model="gpt-4o",
    base_url="https://models.inference.ai.azure.com",
    api_key=os.environ["GITHUB_TOKEN"],
    temperature=0,
)


def _read_pdf(file_path: str) -> str:
    """Extract text from a PDF file."""
    try:
        import pypdf
        reader = pypdf.PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text.strip() or "Could not extract text from PDF."
    except Exception as e:
        return f"Error reading PDF: {e}"


def _read_image(file_path: str) -> str:
    """For images, return a note — GPT-4o vision would need base64 encoding."""
    return f"Image file detected: {Path(file_path).name}. Please ensure this is a clear, readable scan."


def _read_document(file_path: str) -> str:
    """Read document content based on file type."""
    if not os.path.exists(file_path):
        return f"ERROR: File not found at path: {file_path}"

    ext = Path(file_path).suffix.lower()

    if ext == ".pdf":
        return _read_pdf(file_path)
    elif ext == ".txt":
        with open(file_path, "r", errors="ignore") as f:
            return f.read()
    elif ext in (".jpg", ".jpeg", ".png"):
        return _read_image(file_path)
    else:
        return f"Unsupported file type: {ext}. Supported: PDF, TXT, JPG, PNG"


def document_analyzer_agent(state: ImmigrationState) -> dict:
    """
    Agent 2b: Reads uploaded document files, extracts key information,
    checks for issues, and scores overall document readiness.
    """
    profile = state["user_profile"]
    uploaded_docs = profile.get("uploaded_docs", [])
    visa_type = state["visa_recommendation"]["visa_type"]
    checklist = state["document_checklist"]

    # If no documents uploaded, skip gracefully
    if not uploaded_docs:
        result = DocumentAnalysisResult(
            analyzed_documents=[],
            overall_document_score=0,
            critical_issues=["No documents uploaded. All documents marked as missing."],
            documents_verified=[],
            documents_still_missing=[
                d["name"] for d in checklist["documents"] if d["required"]
            ],
            summary="No documents were uploaded for analysis. Please upload your documents and re-run."
        )
        return {
            "document_analysis": result.model_dump(),
            "messages": [{
                "role": "document_analyzer_agent",
                "content": "No documents uploaded. Skipping document analysis."
            }]
        }

    # Read all uploaded documents
    doc_contents = {}
    for path in uploaded_docs:
        content = _read_document(path)
        doc_contents[Path(path).name] = content

    # Required documents from checklist
    required_docs = [d["name"] for d in checklist["documents"] if d["required"]]

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert immigration document reviewer with 20 years of experience.

You have been given the extracted text content of documents uploaded by a visa applicant.
Your job is to:
1. Identify what type each document is (passport, degree certificate, offer letter, etc.)
2. Extract key information from each document (name, dates, institution, expiry, etc.)
3. Identify any issues (expired dates, name mismatch, missing signatures, wrong degree field)
4. Check which required documents are covered vs still missing
5. Give an overall document score 0-100 based on completeness and quality

Required documents for {visa_type}:
{required_docs}

Be specific about issues. If a passport expires in less than 6 months, flag it.
If a degree is in a different field than required, flag it.
If an offer letter is missing salary or job title, flag it."""),
        ("human", """Visa Type: {visa_type}
Applicant Profile: {profile}

Uploaded Documents:
{doc_contents}

Analyze these documents thoroughly.""")
    ])

    structured_llm = llm.with_structured_output(DocumentAnalysisResult, method="function_calling")
    result = (prompt | structured_llm).invoke({
        "visa_type": visa_type,
        "required_docs": json.dumps(required_docs, indent=2),
        "profile": json.dumps(profile, indent=2),
        "doc_contents": json.dumps(doc_contents, indent=2)
    })

    return {
        "document_analysis": result.model_dump(),
        "messages": [{
            "role": "document_analyzer_agent",
            "content": (
                f"Analyzed {len(result.analyzed_documents)} document(s). "
                f"Score: {result.overall_document_score}/100. "
                f"Verified: {len(result.documents_verified)} docs. "
                f"Still missing: {len(result.documents_still_missing)} docs. "
                f"Critical issues: {len(result.critical_issues)}"
            )
        }]
    }
