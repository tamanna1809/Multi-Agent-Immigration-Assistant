import json
import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from state import ImmigrationState, VisaRecommendation
from tools.rag_tool import search_immigration_rules

llm = ChatOpenAI(
    model="gpt-4o",
    base_url="https://models.inference.ai.azure.com",
    api_key=os.environ["GITHUB_TOKEN"],
    temperature=0,
)


def eligibility_agent(state: ImmigrationState) -> dict:
    """Agent 1: Determines the most suitable visa type based on user profile using RAG."""
    profile = state["user_profile"]

    query = (
        f"{profile.get('purpose', '')} visa "
        f"{profile.get('nationality', '')} to {profile.get('target_country', '')}"
    )
    rules = search_immigration_rules.invoke(query)

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert immigration consultant with 20 years of experience.
Based on the user profile and immigration rules retrieved from the knowledge base,
determine the single most suitable visa type.

Set confidence_score:
- Above 0.75 if you have all needed information
- Below 0.60 if critical information is missing (job offer status, education level, visa status)

Immigration Rules Retrieved:
{rules}

Respond with a structured VisaRecommendation."""),
        ("human", "User Profile:\n{profile}\n\nRecommend the best visa type.")
    ])

    structured_llm = llm.with_structured_output(VisaRecommendation, method="function_calling")
    result = (prompt | structured_llm).invoke({
        "rules": rules,
        "profile": json.dumps(profile, indent=2)
    })

    needs_clarification = result.confidence_score < 0.60
    questions = []

    if needs_clarification:
        if profile.get("purpose") == "work" and profile.get("has_job_offer") is None:
            questions.append("Do you have a job offer from an employer in the target country? (yes/no)")
        if not profile.get("education_level"):
            questions.append("What is your highest level of education? (e.g. Bachelor's in Computer Science)")
        if not profile.get("current_visa_status"):
            questions.append("What is your current immigration/visa status in your home country?")

    return {
        "visa_recommendation": result.model_dump(),
        "needs_clarification": needs_clarification,
        "clarification_questions": questions,
        "messages": [{
            "role": "eligibility_agent",
            "content": (
                f"Recommended {result.visa_type} — {result.visa_name} "
                f"({result.confidence_score:.0%} confidence). "
                f"Reasoning: {result.reasoning[:100]}..."
            )
        }]
    }
