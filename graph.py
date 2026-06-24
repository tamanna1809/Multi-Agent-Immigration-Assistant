from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from state import ImmigrationState
from agents.eligibility_agent import eligibility_agent
from agents.document_agent import document_agent
from agents.document_analyzer_agent import document_analyzer_agent
from agents.form_agent import form_agent
from agents.risk_agent import risk_agent
from agents.review_agent import review_agent


def clarification_node(state: ImmigrationState) -> dict:
    """Collects missing information when eligibility agent confidence is too low."""
    profile = dict(state["user_profile"])
    questions = state.get("clarification_questions", [])

    print("\n📋 Additional information needed to proceed:\n")

    for i, question in enumerate(questions, 1):
        answer = input(f"  {i}. {question}\n     Answer: ").strip()

        q_lower = question.lower()
        if "job offer" in q_lower:
            profile["has_job_offer"] = answer.lower() in ("yes", "y", "true", "1")
        elif "education" in q_lower:
            profile["education_level"] = answer
        elif "visa status" in q_lower or "immigration status" in q_lower:
            profile["current_visa_status"] = answer
        elif "criminal" in q_lower:
            profile["criminal_record"] = answer.lower() in ("yes", "y", "true", "1")
        elif "employer" in q_lower or "sponsor" in q_lower:
            profile["employer_sponsored"] = answer.lower() in ("yes", "y", "true", "1")

    print()

    return {
        "user_profile": profile,
        "needs_clarification": False,
        "clarification_questions": [],
        "messages": [{"role": "system", "content": "Clarification collected. Re-running eligibility assessment."}]
    }


def rejection_handler(state: ImmigrationState) -> dict:
    """Handles human rejection — provides structured next-steps guidance."""
    feedback = state.get("human_feedback", "No feedback provided")

    guidance = f"""
╔══════════════════════════════════════════════════════════════════╗
║                    APPLICATION NOT APPROVED                      ║
╚══════════════════════════════════════════════════════════════════╝

 Reviewer Feedback: {feedback}

 Recommended Next Steps:
  1. Review the document checklist and gather all missing documents
  2. Address the risk factors identified in the assessment
  3. Correct any flagged form fields before resubmission
  4. Consider consulting a licensed immigration attorney
  5. Re-run this assessment when the above are addressed

 Your progress has been saved. Run the system again when ready.
"""
    print(guidance)
    return {
        "final_report": guidance,
        "messages": [{"role": "system", "content": "Rejection handled. Next-steps guidance provided to applicant."}]
    }


def route_after_eligibility(state: ImmigrationState) -> str:
    """Conditional: needs more info → clarify, otherwise proceed."""
    if state.get("needs_clarification"):
        return "clarify"
    return "proceed"


def route_after_review(state: ImmigrationState) -> str:
    """Conditional: human approved or rejected."""
    if state.get("human_decision") == "approve":
        return "approved"
    return "rejected"


def build_graph():
    wf = StateGraph(ImmigrationState)

    # Register all nodes
    wf.add_node("eligibility",        eligibility_agent)
    wf.add_node("clarification",      clarification_node)
    wf.add_node("documents",          document_agent)
    wf.add_node("document_analyzer",  document_analyzer_agent)
    wf.add_node("form_filling",       form_agent)
    wf.add_node("risk_assessment",    risk_agent)
    wf.add_node("human_review",       review_agent)
    wf.add_node("rejection",          rejection_handler)

    # Entry point
    wf.set_entry_point("eligibility")

    # Conditional edge after eligibility: clarify or proceed
    wf.add_conditional_edges(
        "eligibility",
        route_after_eligibility,
        {"clarify": "clarification", "proceed": "documents"}
    )

    # Clarification loops back to eligibility (can repeat until confident)
    wf.add_edge("clarification", "eligibility")

    # Linear pipeline
    wf.add_edge("documents",          "document_analyzer")
    wf.add_edge("document_analyzer",  "form_filling")
    wf.add_edge("form_filling",    "risk_assessment")
    wf.add_edge("risk_assessment", "human_review")

    # Conditional edge after human review
    wf.add_conditional_edges(
        "human_review",
        route_after_review,
        {"approved": END, "rejected": "rejection"}
    )

    wf.add_edge("rejection", END)

    memory = MemorySaver()
    return wf.compile(checkpointer=memory)
