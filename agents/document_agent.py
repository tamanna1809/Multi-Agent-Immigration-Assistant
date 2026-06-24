import json
import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from state import ImmigrationState, DocumentChecklist
from tools.rag_tool import search_immigration_rules

llm = ChatOpenAI(
    model="gpt-4o",
    base_url="https://models.inference.ai.azure.com",
    api_key=os.environ["GITHUB_TOKEN"],
    temperature=0,
)


def document_agent(state: ImmigrationState) -> dict:
    """Agent 2: Generates a personalized document checklist based on visa type and user profile."""
    profile = state["user_profile"]
    visa_type = state["visa_recommendation"]["visa_type"]

    rules = search_immigration_rules.invoke(f"{visa_type} required documents checklist complete list")

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a document specialist for immigration applications.
Generate a precise, personalized document checklist for the visa type and applicant profile.

Rules:
- Mark documents as required=True if universally needed for this visa
- Mark required=False for conditional documents (only needed in specific situations)
- Add a 'notes' field explaining any conditions or special requirements
- missing_count should count only the required=True documents since we assume applicant hasn't gathered them yet
- Set ready_to_proceed=False if any required documents are missing

Document Requirements Knowledge Base:
{rules}"""),
        ("human", "Visa Type: {visa_type}\nApplicant Profile:\n{profile}\n\nGenerate the complete personalized document checklist.")
    ])

    structured_llm = llm.with_structured_output(DocumentChecklist, method="function_calling")
    result = (prompt | structured_llm).invoke({
        "rules": rules,
        "visa_type": visa_type,
        "profile": json.dumps(profile, indent=2)
    })

    return {
        "document_checklist": result.model_dump(),
        "messages": [{
            "role": "document_agent",
            "content": (
                f"Generated checklist: {len(result.documents)} documents total, "
                f"{result.missing_count} required documents missing. "
                f"Ready to proceed: {'YES' if result.ready_to_proceed else 'NO'}"
            )
        }]
    }
