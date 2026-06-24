# Multi-Agent Immigration Assistant

An AI-powered Multi-Agent Immigration Assistant built with LangGraph that guides users through the entire visa application process — from eligibility assessment to document analysis, form filling, and risk evaluation — before a human makes the final decision.


---

## What It Does

Most people applying for a visa face the same problem: too many rules, too many documents, and no affordable expert to help. Immigration lawyers charge thousands of dollars. This system does what a lawyer does — and makes it accessible.

Given a user profile and uploaded documents, the system:

1. Recommends the right visa type using retrieved immigration rules
2. Generates a personalized document checklist
3. Reads and analyzes the user's uploaded documents for issues
4. Auto-fills the relevant visa application form
5. Assesses approval probability using live web data
6. Pauses for human review before any final decision is made

---

## Architecture

Five specialized agents connected through shared state, orchestrated by LangGraph:

```
User Input
    └── Guardrail Check
            └── Eligibility Agent         (RAG-powered visa selection)
                    ├── [< 60% confidence] Clarification Node (loops back)
                    └── [≥ 60% confidence] Document Checklist Agent
                                                └── Document Analyzer Agent
                                                        └── Form Agent
                                                                └── Risk Agent
                                                                        └── Human Review Agent
                                                                                ├── [approve] → END
                                                                                └── [reject]  → Rejection Handler → END
```

### Agents

| Agent | Responsibility | Owner |
|---|---|---|
| Eligibility Agent | RAG-powered visa recommendation with confidence scoring | Tamanna |
| Document Checklist Agent | Personalized required/optional document list per visa type | Mahak |
| Document Analyzer Agent | Reads uploaded files, extracts fields, flags issues, scores 0–100 | Mahak |
| Form Agent | Auto-fills DS-160 / IMM-0008 / VAF forms, never touches sensitive fields | Nayanshi |
| Risk Agent | RAG + live Tavily search → approval probability + processing time | Nayanshi |
| Review Agent | Compiles full report, enforces mandatory human approval | Tamanna |

### Tools

| Tool | Purpose |
|---|---|
| FAISS + HuggingFace Embeddings | Local vector search over immigration knowledge base |
| Tavily Web Search | Live USCIS/IRCC/UKVI processing times and policy updates |
| File Reader (pypdf) | Extracts text from uploaded PDF and TXT documents |

---

## Guardrails

- **Input validation** — missing nationality, country, or purpose stops the system before any API call
- **Sensitive field protection** — criminal history, visa refusal history, and health status are never auto-filled
- **Mandatory human-in-the-loop** — the system structurally cannot proceed without a human typing `approve` or `reject`
- **Critical flag detection** — prior rejections, criminal records, high risk, and 5+ missing documents trigger explicit warnings
- **Legal disclaimer** — printed on every single run before any agent executes

---

## Demo Scenarios

Three ready-to-run profiles included:

| Scenario | Applicant | Visa | Risk | Key Detail |
|---|---|---|---|---|
| 1 | Arjun Sharma (Indian) | H-1B | Medium | Offer letter missing signature |
| 2 | Emeka Okonkwo (Nigerian) | F-1 Student | Medium | Ties-to-home-country documents for non-immigrant intent |
| 3 | Ahmed Hassan (Egyptian) | H-1B | **High** | Prior B-1/B-2 rejection in 2022 — critical flag fires |

Switch scenarios in `main.py` (last line):
```python
run(AHMED_PROFILE)   # HIGH risk — most dramatic, run this first
run(ARJUN_PROFILE)   # Clean H-1B approval
run(EMEKA_PROFILE)   # F-1 student, different visa category
```

---

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/your-username/multi-agent-immigration-assistant.git
cd multi-agent-immigration-assistant
```

### 2. Install dependencies

```bash
pip3 install -r requirements.txt
```

### 3. Create a `.env` file

```
GITHUB_TOKEN=your_github_token_here
TAVILY_API_KEY=your_tavily_key_here
LANGCHAIN_API_KEY=your_langsmith_key_here
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=immigration-assistant
```

- **GitHub Token** — [github.com/settings/tokens](https://github.com/settings/tokens) → Generate new token (classic) → No scopes needed → gives free GPT-4o access via GitHub Models
- **Tavily API Key** — [app.tavily.com](https://app.tavily.com) → free tier
- **LangSmith API Key** — [smith.langchain.com](https://smith.langchain.com) → free tier → Settings → API Keys

### 4. Run

```bash
python3 main.py
```

---

## Project Structure

```
immigration-assistant/
├── main.py                        # Entry point + demo profiles
├── graph.py                       # LangGraph StateGraph wiring
├── state.py                       # ImmigrationState + Pydantic models
├── guardrails.py                  # Input validation + critical flag detection
├── agents/
│   ├── eligibility_agent.py
│   ├── document_agent.py
│   ├── document_analyzer_agent.py
│   ├── form_agent.py
│   ├── risk_agent.py
│   └── review_agent.py
├── tools/
│   ├── rag_tool.py                # FAISS + HuggingFace search
│   └── search_tool.py             # Tavily web search
├── data/
│   └── immigration_rules.txt      # US, Canada, UK knowledge base
├── sample_docs/
│   ├── arjun_sharma_h1b/          # 11 documents — H-1B scenario
│   ├── emeka_okonkwo_f1/          # 7 documents — F-1 student scenario
│   └── ahmed_hassan_high_risk/    # 5 documents — high risk scenario
└── evaluation/
    └── test_cases.py              # 5 test cases covering all scenarios
```

---

## Supported Countries

United States · Canada · United Kingdom

---

## Tech Stack

- **LangGraph** — multi-agent orchestration, state management, conditional routing
- **LangChain** — agent framework, tool use, structured outputs
- **GPT-4o** — via GitHub Models (free tier)
- **FAISS** — local vector store for immigration knowledge base
- **HuggingFace Sentence Transformers** — local embeddings (no API key needed)
- **Tavily** — live web search for current processing times
- **LangSmith** — tracing and observability
- **Pydantic** — structured output schemas for every agent
- **pypdf** — PDF text extraction

---

## Disclaimer

This system provides general immigration guidance only. It does not constitute legal advice. For complex cases involving prior rejections or criminal history, consult a licensed immigration attorney.
