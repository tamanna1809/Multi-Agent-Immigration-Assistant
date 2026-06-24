import json
import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from state import ImmigrationState, FilledForm

llm = ChatOpenAI(
    model="gpt-4o",
    base_url="https://models.inference.ai.azure.com",
    api_key=os.environ["GITHUB_TOKEN"],
    temperature=0,
)

FORM_TEMPLATES = {
    "H-1B": {
        "form_name": "DS-160 Nonimmigrant Visa Application",
        "form_id": "DS-160",
        "fields": [
            {"id": "full_name",           "label": "Full Name (as in passport)"},
            {"id": "date_of_birth",       "label": "Date of Birth"},
            {"id": "nationality",         "label": "Nationality/Citizenship"},
            {"id": "passport_number",     "label": "Passport Number"},
            {"id": "passport_expiry",     "label": "Passport Expiry Date"},
            {"id": "employer_name",       "label": "US Employer Name"},
            {"id": "employer_address",    "label": "US Employer Address"},
            {"id": "job_title",           "label": "Job Title / Position"},
            {"id": "annual_salary",       "label": "Annual Salary (USD)"},
            {"id": "education_degree",    "label": "Highest Degree Earned"},
            {"id": "education_field",     "label": "Field of Study"},
            {"id": "travel_history",      "label": "Previous International Travel History"},
            {"id": "previous_us_visa",    "label": "Previous US Visa (type and year)"},
            {"id": "criminal_history",    "label": "Any Criminal History"},
            {"id": "visa_refusal_history","label": "Any Prior Visa Refusal"},
        ]
    },
    "F-1": {
        "form_name": "DS-160 Student Visa Application",
        "form_id": "DS-160-F1",
        "fields": [
            {"id": "full_name",         "label": "Full Name (as in passport)"},
            {"id": "date_of_birth",     "label": "Date of Birth"},
            {"id": "nationality",       "label": "Nationality/Citizenship"},
            {"id": "passport_number",   "label": "Passport Number"},
            {"id": "passport_expiry",   "label": "Passport Expiry Date"},
            {"id": "school_name",       "label": "Name of US Institution"},
            {"id": "program_name",      "label": "Program/Course of Study"},
            {"id": "program_start",     "label": "Program Start Date"},
            {"id": "financial_sponsor", "label": "Financial Sponsor Name"},
            {"id": "sponsor_relation",  "label": "Sponsor Relationship to Applicant"},
            {"id": "annual_tuition",    "label": "Annual Tuition Amount (USD)"},
            {"id": "living_expenses",   "label": "Estimated Annual Living Expenses"},
            {"id": "ties_home_country", "label": "Ties to Home Country (family, property, job)"},
            {"id": "criminal_history",  "label": "Any Criminal History"},
            {"id": "visa_refusal",      "label": "Any Prior Visa Refusal"},
        ]
    },
    "Express Entry": {
        "form_name": "Canada Express Entry Application (IMM 0008)",
        "form_id": "IMM-0008",
        "fields": [
            {"id": "full_name",          "label": "Full Legal Name"},
            {"id": "date_of_birth",      "label": "Date of Birth"},
            {"id": "nationality",        "label": "Country of Citizenship"},
            {"id": "passport_number",    "label": "Passport Number"},
            {"id": "current_country",    "label": "Current Country of Residence"},
            {"id": "language_score",     "label": "IELTS/CELPIP Score"},
            {"id": "education_level",    "label": "Highest Education Level"},
            {"id": "years_experience",   "label": "Years of Skilled Work Experience"},
            {"id": "noc_code",           "label": "NOC Occupation Code"},
            {"id": "province_interest",  "label": "Preferred Province"},
            {"id": "family_in_canada",   "label": "Family Members in Canada"},
            {"id": "criminal_record",    "label": "Criminal Record"},
            {"id": "health_status",      "label": "Health Conditions"},
        ]
    },
    "Skilled Worker Visa": {
        "form_name": "UK Skilled Worker Visa Application (VAF)",
        "form_id": "VAF-SKW",
        "fields": [
            {"id": "full_name",           "label": "Full Name"},
            {"id": "date_of_birth",       "label": "Date of Birth"},
            {"id": "nationality",         "label": "Nationality"},
            {"id": "passport_number",     "label": "Passport Number"},
            {"id": "cos_reference",       "label": "Certificate of Sponsorship Reference"},
            {"id": "employer_name",       "label": "UK Employer Name"},
            {"id": "job_title",           "label": "Job Title"},
            {"id": "annual_salary",       "label": "Annual Salary (GBP)"},
            {"id": "english_test",        "label": "English Language Test (IELTS/equivalent)"},
            {"id": "criminal_history",    "label": "Criminal History"},
            {"id": "previous_uk_visa",    "label": "Previous UK Visa"},
        ]
    }
}

SENSITIVE_FIELDS = {"criminal_history", "visa_refusal_history", "visa_refusal", "criminal_record", "health_status"}


def form_agent(state: ImmigrationState) -> dict:
    """Agent 3: Auto-fills application form fields from user profile, flags sensitive fields for human review."""
    profile = state["user_profile"]
    visa_type = state["visa_recommendation"]["visa_type"]

    # Find matching form template
    template = FORM_TEMPLATES.get(visa_type)
    if not template:
        # Fall back to H-1B form for unknown visa types
        template = FORM_TEMPLATES["H-1B"]

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a form-filling specialist for immigration applications.

Fill in form fields using the applicant's profile data.

Rules (STRICTLY follow these):
1. Set auto_filled=True and provide value for fields you can fill from profile data
2. ALWAYS set needs_review=True for these sensitive fields: {sensitive_fields}
3. Set needs_review=True for fields where data is ambiguous or missing
4. Leave value=null for fields with no data in the profile
5. For needs_review=True fields, provide a clear review_reason
6. Calculate completion_percentage as: (auto_filled fields / total fields) * 100
7. flagged_fields should list the field_id of every needs_review=True field"""),
        ("human", """Form Template:
{template}

Applicant Profile:
{profile}

Fill this form. Remember: always flag sensitive fields for human review.""")
    ])

    structured_llm = llm.with_structured_output(FilledForm, method="function_calling")
    result = (prompt | structured_llm).invoke({
        "sensitive_fields": ", ".join(SENSITIVE_FIELDS),
        "template": json.dumps(template, indent=2),
        "profile": json.dumps(profile, indent=2)
    })

    return {
        "filled_form": result.model_dump(),
        "messages": [{
            "role": "form_agent",
            "content": (
                f"Form '{result.form_name}' ({result.form_id}): "
                f"{result.completion_percentage:.0f}% auto-filled. "
                f"Fields needing human review: {', '.join(result.flagged_fields) or 'None'}"
            )
        }]
    }
