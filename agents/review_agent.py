from state import ImmigrationState
from guardrails import check_critical_flags

SEP = "-" * 66


def review_agent(state: ImmigrationState) -> dict:
    """Agent 5: Human-in-the-loop. Presents full compiled report and requires human approval before any action."""

    v = state["visa_recommendation"]
    d = state["document_checklist"]
    f = state["filled_form"]
    r = state["risk_assessment"]
    da = state.get("document_analysis")

    # Critical flags
    flags = check_critical_flags(state)
    flags_section = ""
    if flags:
        flag_lines = "\n".join(f"   * {fl}" for fl in flags)
        flags_section = f"\n WARNING — CRITICAL FLAGS:\n{flag_lines}\n"

    # Risk factors
    risk_lines = "\n".join(
        f"   [{x['severity'].upper():6}] {x['category']}: {x['description']}\n"
        f"            -> {x['mitigation_advice']}"
        for x in r["risk_factors"]
    )

    # Document checklist
    doc_lines = "\n".join(
        f"   {'[OK]' if doc['status'] == 'provided' else '[X] '} "
        f"{'[REQUIRED]' if doc['required'] else '[OPTIONAL]'} {doc['name']}"
        + (f"\n     Note: {doc['notes']}" if doc.get("notes") else "")
        for doc in d["documents"]
    )

    # Document analysis section — built separately to avoid f-string nesting issues
    doc_analysis_section = ""
    if da:
        issues = da.get("critical_issues", [])
        issue_lines = "\n".join(f"   * {i}" for i in issues) if issues else "   None"
        verified = ", ".join(da.get("documents_verified", [])) or "None"
        missing  = ", ".join(da.get("documents_still_missing", [])) or "None"
        score    = da.get("overall_document_score", "N/A")
        summary  = da.get("summary", "")
        doc_analysis_section = (
            f"\n{SEP}\n"
            f" 2b. DOCUMENT ANALYSIS  (Score: {score}/100)\n"
            f"{SEP}\n"
            f"   Verified Documents : {verified}\n"
            f"   Still Missing      : {missing}\n"
            f"   Critical Issues    :\n{issue_lines}\n"
            f"   Summary            : {summary}\n"
        )

    report = (
        f"\n{'=' * 66}\n"
        f"        AI IMMIGRATION ASSISTANT -- REVIEW REPORT\n"
        f"{'=' * 66}\n"
        f"{flags_section}\n"
        f"{SEP}\n"
        f" 1. VISA RECOMMENDATION\n"
        f"{SEP}\n"
        f"   Recommended : {v['visa_type']} -- {v['visa_name']}\n"
        f"   Confidence  : {v['confidence_score']:.0%}\n"
        f"   Reasoning   : {v['reasoning']}\n"
        f"   Alternatives: {', '.join(v.get('alternative_visas', [])) or 'None identified'}\n"
        f"\n{SEP}\n"
        f" 2. DOCUMENT CHECKLIST  ({d['missing_count']} missing)\n"
        f"{SEP}\n"
        f"{doc_lines}\n\n"
        f"   Ready to Proceed: {'YES' if d['ready_to_proceed'] else 'NO -- gather missing documents first'}\n"
        f"{doc_analysis_section}"
        f"\n{SEP}\n"
        f" 3. FORM STATUS -- {f['form_name']} ({f['form_id']})\n"
        f"{SEP}\n"
        f"   Completion  : {f['completion_percentage']:.0f}% auto-filled\n"
        f"   Needs Review: {', '.join(f['flagged_fields']) if f['flagged_fields'] else 'None'}\n"
        f"\n{SEP}\n"
        f" 4. RISK ASSESSMENT\n"
        f"{SEP}\n"
        f"   Overall Risk    : {r['overall_risk_level'].upper()}\n"
        f"   Approval Chance : {r['approval_probability_pct']}%\n"
        f"   Processing Time : {r['estimated_processing_days_min']}-{r['estimated_processing_days_max']} days\n\n"
        f"   Risk Factors:\n{risk_lines}\n"
        f"\n{SEP}\n"
        f" 5. FINAL RECOMMENDATION\n"
        f"{SEP}\n"
        f"   {r['final_recommendation']}\n"
        f"\n{'=' * 66}\n"
        f" WARNING: HUMAN APPROVAL REQUIRED -- Nothing is filed without your consent\n"
        f"{'=' * 66}\n"
    )

    print(report)

    while True:
        decision = input(" Your decision -- type 'approve' or 'reject': ").strip().lower()
        if decision in ("approve", "reject"):
            break
        print(" Please type exactly 'approve' or 'reject'.")

    feedback = ""
    if decision == "reject":
        feedback = input(" Feedback / reason for rejection: ").strip()
        print(f"\n Noted. Application not submitted. Feedback: {feedback}\n")
    else:
        print("\n Application approved by reviewer. Proceeding...\n")

    return {
        "human_decision": decision,
        "human_feedback": feedback,
        "final_report": report,
        "messages": [{
            "role": "human_reviewer",
            "content": f"Human decision: {decision.upper()}. Feedback: '{feedback}'"
        }]
    }
