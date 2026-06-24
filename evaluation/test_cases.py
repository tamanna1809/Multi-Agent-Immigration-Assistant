"""
Evaluation test suite — 5 test cases covering different scenarios.
Run: python evaluation/test_cases.py
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

TEST_CASES = [
    {
        "id": "TC-001",
        "label": "Standard H-1B Tech Worker",
        "description": "Indian software engineer with US job offer and employer sponsorship",
        "profile": {
            "name": "Priya Patel",
            "nationality": "Indian",
            "current_country": "India",
            "target_country": "United States",
            "purpose": "work",
            "education_level": "Master's in Computer Science",
            "has_job_offer": True,
            "employer_sponsored": True,
            "current_visa_status": "None",
            "annual_income_usd": 120000,
            "previous_visa_rejection": False,
        },
        "expected_visa": "H-1B",
        "expected_risk": "medium",
        "notes": "Medium risk due to H-1B lottery. All other criteria strong.",
    },
    {
        "id": "TC-002",
        "label": "International Student",
        "description": "Nigerian student admitted to a US university",
        "profile": {
            "name": "Emeka Okonkwo",
            "nationality": "Nigerian",
            "current_country": "Nigeria",
            "target_country": "United States",
            "purpose": "study",
            "education_level": "Completed secondary school",
            "has_job_offer": False,
            "current_visa_status": "None",
            "annual_income_usd": 0,
            "previous_visa_rejection": False,
        },
        "expected_visa": "F-1",
        "expected_risk": "medium",
        "notes": "Nigerian applicants face higher scrutiny. Financial proof critical.",
    },
    {
        "id": "TC-003",
        "label": "Canada Express Entry",
        "description": "British software engineer targeting Canadian permanent residence",
        "profile": {
            "name": "James Wilson",
            "nationality": "British",
            "current_country": "United Kingdom",
            "target_country": "Canada",
            "purpose": "work",
            "education_level": "Bachelor's in Software Engineering",
            "has_job_offer": False,
            "employer_sponsored": False,
            "current_visa_status": "British citizen",
            "annual_income_usd": 85000,
            "previous_visa_rejection": False,
        },
        "expected_visa": "Express Entry",
        "expected_risk": "low",
        "notes": "Strong profile, British citizen, high salary, no red flags.",
    },
    {
        "id": "TC-004",
        "label": "High Risk — Prior Visa Rejection",
        "description": "Egyptian applicant with previous US visa rejection",
        "profile": {
            "name": "Ahmed Hassan",
            "nationality": "Egyptian",
            "current_country": "Egypt",
            "target_country": "United States",
            "purpose": "work",
            "education_level": "Bachelor's in Business Administration",
            "has_job_offer": True,
            "employer_sponsored": True,
            "current_visa_status": "Previously rejected B-1/B-2",
            "annual_income_usd": 75000,
            "previous_visa_rejection": True,
        },
        "expected_visa": "H-1B",
        "expected_risk": "high",
        "notes": "Prior rejection is a major red flag. System should flag this prominently.",
    },
    {
        "id": "TC-005",
        "label": "Incomplete Profile — Triggers Clarification Flow",
        "description": "Mexican applicant with minimal information to test clarification branching",
        "profile": {
            "name": "Maria Garcia",
            "nationality": "Mexican",
            "current_country": "Mexico",
            "target_country": "United States",
            "purpose": "work",
            # Intentionally missing: education_level, has_job_offer, current_visa_status
        },
        "expected_visa": "TBD after clarification",
        "expected_risk": "unknown",
        "notes": "Should trigger clarification node due to low confidence. Tests conditional edge.",
    },
]


def print_test_summary():
    print("=" * 66)
    print("  IMMIGRATION ASSISTANT — EVALUATION TEST CASES")
    print("=" * 66)
    for tc in TEST_CASES:
        print(f"\n  [{tc['id']}] {tc['label']}")
        print(f"  Description : {tc['description']}")
        print(f"  Expected    : Visa={tc['expected_visa']}, Risk={tc['expected_risk']}")
        print(f"  Notes       : {tc['notes']}")
    print("\n" + "=" * 66)
    print(f"  Total test cases: {len(TEST_CASES)}")
    print("=" * 66)


def run_single_test(tc: dict, auto_approve: bool = True):
    """Run a single test case. Set auto_approve=False to interact manually."""
    import unittest.mock as mock
    from main import run

    print(f"\n{'='*66}")
    print(f"  Running {tc['id']}: {tc['label']}")
    print(f"{'='*66}")

    if auto_approve:
        with mock.patch("builtins.input", return_value="approve"):
            try:
                run(tc["profile"])
                return {"id": tc["id"], "status": "PASS"}
            except Exception as e:
                return {"id": tc["id"], "status": "FAIL", "error": str(e)}
    else:
        try:
            run(tc["profile"])
            return {"id": tc["id"], "status": "PASS"}
        except Exception as e:
            return {"id": tc["id"], "status": "FAIL", "error": str(e)}


if __name__ == "__main__":
    print_test_summary()
    print("\nTo run a specific test case interactively:")
    print("  from evaluation.test_cases import TEST_CASES, run_single_test")
    print("  run_single_test(TEST_CASES[0], auto_approve=False)")
