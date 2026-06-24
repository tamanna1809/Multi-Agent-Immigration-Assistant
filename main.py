import os
import sys
from dotenv import load_dotenv

load_dotenv()

# LangSmith tracing
os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
os.environ.setdefault("LANGCHAIN_PROJECT", "immigration-assistant")

from graph import build_graph
from guardrails import validate_user_profile, DISCLAIMER
from state import ImmigrationState


def run(user_profile: dict):
    print(DISCLAIMER)

    valid, msg = validate_user_profile(user_profile)
    if not valid:
        print(f"\n❌ Cannot proceed: {msg}\n")
        sys.exit(1)

    graph = build_graph()

    initial_state: ImmigrationState = {
        "user_profile":            user_profile,
        "visa_recommendation":     None,
        "document_checklist":      None,
        "document_analysis":       None,
        "filled_form":             None,
        "risk_assessment":         None,
        "human_decision":          None,
        "human_feedback":          None,
        "needs_clarification":     False,
        "clarification_questions": [],
        "messages":                [],
        "errors":                  [],
        "final_report":            None,
    }

    config = {
        "configurable": {
            "thread_id": user_profile.get("name", "applicant").replace(" ", "_").lower()
        }
    }

    name = user_profile.get("name", "Applicant")
    print(f"\n{'='*66}")
    print(f"  Starting Immigration Assessment for: {name}")
    print(f"  {user_profile.get('nationality')} → "
          f"{user_profile.get('target_country')} ({user_profile.get('purpose')})")
    print(f"{'='*66}\n")

    step_count = 0
    for step in graph.stream(initial_state, config=config):
        node_name = list(step.keys())[0]
        node_output = step[node_name]
        for msg in node_output.get("messages", []):
            step_count += 1
            role = msg.get("role", "system")
            content = msg.get("content", "")
            print(f"  [{step_count:02d}] [{role}]\n       {content}\n")

    print(f"\n{'='*66}")
    print("  Immigration assessment complete.")
    print(f"{'='*66}\n")


# ── SCENARIO 1: Arjun Sharma — Indian H-1B Tech Worker (MEDIUM risk) ──────────
ARJUN_PROFILE = {
    "name":                    "Arjun Sharma",
    "nationality":             "Indian",
    "current_country":         "India",
    "target_country":          "United States",
    "purpose":                 "work",
    "education_level":         "Bachelor's in Computer Science",
    "has_job_offer":           True,
    "employer_sponsored":      True,
    "current_visa_status":     "No current US visa",
    "annual_income_usd":       95000,
    "previous_visa_rejection": False,
    "uploaded_docs": [
        "sample_docs/arjun_sharma_h1b/passport.txt",
        "sample_docs/arjun_sharma_h1b/degree_certificate.txt",
        "sample_docs/arjun_sharma_h1b/academic_transcripts.txt",
        "sample_docs/arjun_sharma_h1b/offer_letter.txt",
        "sample_docs/arjun_sharma_h1b/i129_petition.txt",
        "sample_docs/arjun_sharma_h1b/i129_approval_notice.txt",
        "sample_docs/arjun_sharma_h1b/bank_statement.txt",
        "sample_docs/arjun_sharma_h1b/employment_verification.txt",
        "sample_docs/arjun_sharma_h1b/resume_cv.txt",
        "sample_docs/arjun_sharma_h1b/ds160_confirmation.txt",
        "sample_docs/arjun_sharma_h1b/mrv_fee_receipt.txt",
    ]
}

# ── SCENARIO 2: Emeka Okonkwo — Nigerian F-1 Student (MEDIUM risk) ─────────────
EMEKA_PROFILE = {
    "name":                    "Emeka Okonkwo",
    "nationality":             "Nigerian",
    "current_country":         "Nigeria",
    "target_country":          "United States",
    "purpose":                 "study",
    "education_level":         "Completed secondary school (Kings College Lagos)",
    "has_job_offer":           False,
    "employer_sponsored":      False,
    "current_visa_status":     "No current US visa",
    "annual_income_usd":       0,
    "previous_visa_rejection": False,
    "uploaded_docs": [
        "sample_docs/emeka_okonkwo_f1/passport.txt",
        "sample_docs/emeka_okonkwo_f1/university_acceptance.txt",
        "sample_docs/emeka_okonkwo_f1/i20_form.txt",
        "sample_docs/emeka_okonkwo_f1/sevis_fee_receipt.txt",
        "sample_docs/emeka_okonkwo_f1/financial_proof.txt",
        "sample_docs/emeka_okonkwo_f1/ties_to_home_country.txt",
        "sample_docs/emeka_okonkwo_f1/toefl_scores.txt",
    ]
}

# ── SCENARIO 3: Ahmed Hassan — Egyptian H-1B with Prior Rejection (HIGH risk) ──
AHMED_PROFILE = {
    "name":                    "Ahmed Hassan",
    "nationality":             "Egyptian",
    "current_country":         "Egypt",
    "target_country":          "United States",
    "purpose":                 "work",
    "education_level":         "Bachelor's in Business Administration",
    "has_job_offer":           True,
    "employer_sponsored":      True,
    "current_visa_status":     "Previously rejected B-1/B-2 visa (2022)",
    "annual_income_usd":       75000,
    "previous_visa_rejection": True,
    "uploaded_docs": [
        "sample_docs/ahmed_hassan_high_risk/passport.txt",
        "sample_docs/ahmed_hassan_high_risk/degree_certificate.txt",
        "sample_docs/ahmed_hassan_high_risk/offer_letter.txt",
        "sample_docs/ahmed_hassan_high_risk/employment_verification.txt",
        "sample_docs/ahmed_hassan_high_risk/prior_rejection_explanation.txt",
    ]
}

if __name__ == "__main__":
    # ── Switch between scenarios here for the demo ──
    # Change ARJUN_PROFILE to EMEKA_PROFILE or AHMED_PROFILE to test others
    run(ARJUN_PROFILE)
