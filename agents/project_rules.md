# Project Rules - Interview Practice App Specific

These are rules specific to the Interview Practice App project. They must be applied on top of the general rules.

---

## PRD ALIGNMENT

1. **ALWAYS align implementation with PRD and documented requirements**
2. **ALWAYS implement features exactly as defined in PRD schemas and flows**
3. **NEVER introduce features not defined in requirements without confirmation**
4. Start with `PRODUCT_REQUIREMENT_DOCUMENT.md` as the primary source of truth

---

## FILE SIZE CONSTRAINT

- All files (Markdown and code) must not exceed 250 lines

---

## SCHEMA ENFORCEMENT

1. **ALWAYS respect defined schemas and structured outputs**
2. **ALWAYS validate LLM outputs against expected JSON schema**
3. Use Pydantic for schema validation

---

## EVALUATION & SCORING

1. **NEVER deviate from evaluation dimensions, scoring, or report structure**
2. Always validate and sanitize LLM outputs before using them for scoring

---

## REPORT STRUCTURE

1. Follow the exact report structure as defined in PRD
2. Generate JSON/PDF reports only in the formats specified

---

## OPENROUTER USAGE

- OpenRouter is the API gateway for this project
- Use the **openai SDK** (`openai` package) to call OpenRouter
- Set `base_url="https://openrouter.ai/v1"` in the client config
- Same interface as calling OpenAI directly
- **openai package is used ONLY as a client to access OpenRouter - No direct OpenAI API usage**

```python
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/v1"
)
```

---

## WORKFLOW CONSTRAINTS

### Development Workflow
1. **Read PRD** - Start with `PRODUCT_REQUIREMENT_DOCUMENT.md` (source of truth)
2. **Create requirements.txt** - Define dependencies first
3. **Setup environment** - Create `.env.example`, configure API key
4. **Build core modules** - Implement app.py, prompts.py, config.py, utils/
5. **Validate against PRD schemas, flows, and constraints** - Ensure all requirements are covered
6. **Run lint + manual test** - `ruff .` and `streamlit run app.py`
7. **Iterate** - Repeat steps 4-6 until complete

### Key functions needed:
- `call_openrouter(prompt, settings)` - API call
- `validate_input(user_input)` - security guard
- `get_session_state()` - maintain chat history

---

## OPENROUTER API NOTE

- OpenRouter is an API gateway (provides unified API for multiple LLMs)
- Use the **openai SDK** (`openai` package) to call OpenRouter
- Set `base_url="https://openrouter.ai/v1"` in the client config
- Same interface as calling OpenAI directly
- **openai package is used ONLY as a client to access OpenRouter - No direct OpenAI API usage**

---

## ENVIRONMENT VARIABLES

```
OPENROUTER_API_KEY=your_api_key_here
```

---

## DEPENDENCY TRACKING

### Python Packages (in requirements.txt)
```
streamlit==1.40.0
openai==1.55.0
python-dotenv==1.0.1
ruff==0.8.0
reportlab==4.0.0          # PDF generation (choose ONE)
# weasyprint==60.0         # alt: PDF generation
pydantic==2.10.0         # Schema validation
```

---

## CV/SESSION CONSTRAINTS

- Enforce session-only CV storage (aligns with PRD - no persistence)
- Never store CV data beyond the current session
- Validate CV input before processing

---

## TESTING (LLM/JSON Specific)

### Test Cases
- Test JSON schema compliance
- Test prompt injection cases
- Test API failure scenarios
- Test malformed or invalid JSON responses from LLM

### Test Commands
```bash
# Run lint
ruff .

# Run app
streamlit run app.py
```

---

## DOCUMENTATION UPDATES

1. Update `doc/manual.md` after every code change with the current user-facing behaviour.
2. Update `doc/developer-manual.md` after every code change with the current implementation details.
3. Update `doc/test-manual.md` after every code change with the current manual UI test steps.
4. Keep all three files aligned with the actual implemented code state.

---

## PROJECT INDEX

### DOC DEPENDENCY ORDER (read in this sequence)
```
PRD → Architecture → Features → Mockups
```

### ROOT FILES
| File | Purpose |
|------|---------|
| `115.md` | Sprint project requirements & task description |
| `AGENTS.md` | This file - rules for AI agents |
| `.gitignore` | Git ignore patterns |

### DOCUMENTATION (doc/product_requirement/)
| File | Purpose |
|------|---------|
| `PRODUCT_REQUIREMENT_DOCUMENT.md` | **PRIMARY SOURCE OF TRUTH** - Full product specification |
| `product-requirements.md` | Detailed requirements |
| `high-level-architecture.md` | System architecture design |
| `features.md` | Feature list |
| `minimum-viable-product-mvp.md` | MVP scope |
| `use-cases.md` | User scenarios |
| `user-interface--screens.md` | UI/UX specs |
| `user-pain-points.md` | Problem statements |
| `success-metrics.md` | KPIs |
| `edge-cases--security-considerations.md` | Security & edge cases |

### DOCUMENTATION - Mockups
| File | Purpose |
|------|---------|
| `mock_ups/1-welcome screen.md` | Welcome screen UI |
| `mock_ups/2-Set up screen.md` | Setup/interview config UI |
| `mock_ups/3-Question & Answer.md` | Q&A session UI |
| `mock_ups/4-Feedback.md` | AI feedback UI |
| `mock_ups/5-Sample Answer.md` | Sample answers UI |
| `mock_ups/6-Follow-Base-Exit.md` | Follow-up questions UI |
| `mock_ups/7-Session-Summary.md` | Session summary UI |

### DOCUMENTATION - Architecture Diagrams
| File | Purpose |
|------|---------|
| `architecture_&_flow_diagram/index.md` | Architecture overview |
| `architecture_&_flow_diagram/High_Level_Architecture.png` | System diagram |
| `architecture_&_flow_diagram/Navigation Flow.png` | User flow |
| `architecture_&_flow_diagram/CV_Extraction_&_Structuring.png` | CV processing |
| `architecture_&_flow_diagram/Gap_Analysis_&_Targeted_Questioning.png` | Gap analysis |
| `architecture_&_flow_diagram/Question_Generation_with_Distribution.png` | Question generation |

### CODE FILES (To Be Created)
| File | Purpose | Priority |
|------|---------|----------|
| `app.py` | Main Streamlit application | REQUIRED |
| `requirements.txt` | Python dependencies | REQUIRED |
| `.env` | Environment variables | REQUIRED |
| `.env.example` | Env template | REQUIRED |
| `prompts.py` | System prompts library | RECOMMENDED |
| `config.py` | Model settings | RECOMMENDED |
| `utils/api_client.py` | OpenRouter API wrapper | RECOMMENDED |
| `utils/security.py` | Input validation | RECOMMENDED |
| `utils/session_manager.py` | Session state | OPTIONAL |
| `utils/evaluator.py` | Scoring + parsing | OPTIONAL |
| `utils/report_generator.py` | PDF/JSON logic | OPTIONAL |
| `utils/error_handler.py` | Centralised error handling | OPTIONAL |
| `tests/test_app.py` | Unit tests | OPTIONAL |

---

## QUICK COMMANDS

```bash
# Install deps
pip install -r requirements.txt

# Run app
streamlit run app.py

# Set API key
export OPENROUTER_API_KEY="your-key"
```
