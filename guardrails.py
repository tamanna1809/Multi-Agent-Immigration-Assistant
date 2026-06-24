from state import ImmigrationState

DISCLAIMER = """
╔══════════════════════════════════════════════════════════════╗
║                      ⚠️  DISCLAIMER                          ║
║  This system provides general immigration guidance only.     ║
║  It does NOT constitute legal advice. For complex cases      ║
║  (prior rejections, criminal history), consult a licensed    ║
║  immigration attorney before proceeding.                     ║
╚══════════════════════════════════════════════════════════════╝
"""

VALID_PURPOSES = ["work", "study", "family", "travel", "business"]
VALID_COUNTRIES = ["United States", "Canada", "United Kingdom", "Australia", "Germany"]


def validate_user_profile(profile: dict) -> tuple[bool, str]:
    required = ["nationality", "target_country", "purpose"]
    missing = [f for f in required if not profile.get(f)]
    if missing:
        return False, f"Missing required fields: {', '.join(missing)}"

    if profile.get("purpose") not in VALID_PURPOSES:
        return False, f"Purpose must be one of: {', '.join(VALID_PURPOSES)}"

    if profile.get("target_country") not in VALID_COUNTRIES:
        return False, f"Supported countries: {', '.join(VALID_COUNTRIES)}"

    return True, "OK"


def check_critical_flags(state: ImmigrationState) -> list[str]:
    flags = []
    profile = state.get("user_profile", {})

    if profile.get("previous_visa_rejection"):
        flags.append("CRITICAL: Prior visa rejection detected — must be disclosed on all forms.")

    if profile.get("criminal_record"):
        flags.append("CRITICAL: Criminal record may affect eligibility — legal consultation strongly recommended.")

    risk = state.get("risk_assessment") or {}
    if risk.get("overall_risk_level") == "high":
        flags.append("HIGH RISK: This application has a high rejection probability. Recommend attorney review.")

    docs = state.get("document_checklist") or {}
    if docs.get("missing_count", 0) > 5:
        flags.append(f"WARNING: {docs['missing_count']} required documents are missing. Do not proceed until gathered.")

    return flags
