# Product Requirement Document (PRD)
## Interview Practice App v1.0 — AI-Powered Interview Preparation Platform

**Document Version:** 1.0  
**Date:** April 2026  
**Status:** Planned MVP  
**Audience:** Developers, QA, Stakeholders, Product Managers

---

## Table of Contents

1. [Product Overview](#product-overview)
2. [Problem Statement](#problem-statement)
3. [Real-World Value](#real-world-value)
4. [User Pain Points](./user-pain-points.md)
5. [Product Requirements](./product-requirements.md)
6. [Minimum Viable Product (MVP)](./minimum-viable-product-mvp.md)
7. [High-Level Architecture](./high-level-architecture.md)
   - [Architecture & Flow Diagrams](./architecture_&_flow_diagram/index.md)
8. [User Interface & Screens](./user-interface--screens.md)
9. [Features](./features.md)
10. [Use Cases](./use-cases.md)
11. [Edge Cases & Security](./edge-cases--security-considerations.md)
12. [Success Metrics](./success-metrics.md)

---

## Product Overview

### What is the Interview Practice App?

The **Interview Practice App** is an AI-powered platform that simulates realistic technical and behavioural interviews through adaptive, context-aware questioning and structured evaluation.

It generates personalised interview scenarios based on the user’s target role, experience, CV, and job description, and provides immediate diagnostic feedback across five defined dimensions: relevance, structure, specificity, communication, and problem-solving approach.

The platform is designed to enable candidates to systematically improve how they think, communicate, and justify their decisions within interview settings.

### Vision

Enable professionals to practise interviews in a realistic, low-pressure environment, supported by personalised, adaptive coaching aligned to their role, experience level, and learning pace.

### Target Users

- Technical candidates (e.g. Backend Engineers, Frontend Engineers, Data Scientists)
- Career changers preparing for career transitions
- Professionals preparing for high-stakes interviews
- Students preparing for internships and entry-level roles
- Experienced professionals refining their communication, reasoning, and decision-making for senior roles

### Key Differentiators

| Feature                | Interview Practice App                                   | Traditional Coaching | Generic Question Banks |
| ---------------------- | -------------------------------------------------------- | -------------------- | ---------------------- |
| Real-time feedback     | ✓ AI-powered, immediate                                  | Delayed (human-led)  | ✗ None                 |
| Adaptive questioning   | ✓ Dynamic, performance-driven follow-ups                 | Semi-structured      | ✗ Static               |
| Interviewer simulation | ✓ Configurable personas (e.g. Friendly, Neutral, Strict) | Limited variation    | ✗ None                 |
| Structured evaluation  | ✓ Standardised scoring (JSON + visual outputs)           | Subjective           | ✗ None                 |
| Cost                   | Low (API-based)                                          | High (human-led)     | Low (limited value)    |
| Availability           | 24/7 on-demand                                           | Limited availability | Always available       |
| Personalisation        | ✓ Role, difficulty, and **job description-based**        | High (human-led)     | ✗ None                 |
| Reasoning evaluation   | ✓ Evaluates decision-making and trade-offs               | Limited              | ✗ None                 |

---

## Problem Statement

### The Challenge

Professionals preparing for technical interviews face several structural barriers:

#### Limited Access to Practice
- Live mock interviews are expensive ($50–$200/hour)  
- Sourcing qualified interviewers is time-consuming  
- Scheduling constraints reduce consistency and frequency of practice  

#### Lack of Adaptive Feedback
- Most resources rely on generic question sets  
- Limited or no real-time evaluation of responses  
- Little guidance on why an answer is weak or how it can be improved  

#### Inconsistent Interviewer Experience
- Human interviewers apply varying standards and communication styles  
- No clear or consistent benchmark for what constitutes a strong answer  
- Lack of standardisation increases uncertainty and anxiety  

#### Weak Learning Feedback Loop
- Candidates lack clarity on which skills require improvement  
- No aggregation of insights across practice sessions  
- Limited ability to measure progress over time  

#### Role and Context Misalignment
- Practice questions often fail to reflect the target role or job requirements  
- Generic feedback does not address domain-specific expectations  
- Difficulty levels are inconsistent or misaligned with real interview standards  

These challenges result in inefficient preparation, reduced confidence, and repeated performance gaps in high-stakes interviews.

### Why This Matters

Candidates who practise with structured, adaptive feedback demonstrate materially stronger performance in real interviews. However, most interview preparation remains unstructured, resulting in:
- Inefficient use of practice time 
- Reduced confidence when entering interviews 
- Repetition of the same mistakes across multiple attempts 
- Lower success rates in competitive selection processes

---

## Real-World Value

### Business Value

1. **Accessibility**
   - Cost-effective alternative to traditional coaching models
   - Available 24/7, enabling flexible, self-paced practice

2. **Scalability**
   - Supports high user volumes without reliance on human interviewers
   - Scales efficiently to meet demand with a consistent user experience

3. **Data-Driven Insights**
   - Enables collection of anonymised performance data to identify common skill gaps
   - Supports continuous improvement of question generation and evaluation models

4. **Revenue Opportunities**
   - Freemium model (core functionality free, advanced reports and features paid)
   - B2B licensing for universities, training providers, and corporate programmes
   - Potential integration with recruitment and job platforms

5. **Standardisation**
   - Provides consistent evaluation criteria across all users
   - Reduces variability inherent in human-led interview preparation

### User Value

1. Learning and Improvement  
   - Structured feedback identifies specific areas for improvement  
   - Adaptive follow-ups target weaker areas and reinforce learning  
   - Session reports enable tracking of progress over time  

2. Confidence Building  
   - Provides a low-pressure environment for repeated practice  
   - Configurable interviewer personas (e.g. friendly, neutral, strict) support progressive challenge  
   - Simulates realistic interview conditions  

3. Time Efficiency  
   - Eliminates the need for scheduling  
   - Provides immediate feedback without reliance on external reviewers  
   - Enables multiple practice iterations within a single session  

4. Competitive Advantage  
   - Improves interview readiness through structured preparation  
   - Strengthens ability to articulate experience and decision-making  
   - Reduces interview-related uncertainty and anxiety  

5. Decision-Making Clarity  
   - Develops the ability to explain reasoning and trade-offs  
   - Improves how users justify technical and behavioural decisions in interviews  

---

## Conclusion

The **Interview Practice App** is a viable, valuable product that solves real interview preparation pain points. The product follows a phased delivery model. Phase 1 defines the minimum viable product required for functional delivery. Subsequent phases extend the system with advanced personalisation, reasoning evaluation, and reporting capabilities.

### MVP Delivers:

✓ Realistic interview simulation  
✓ Personalized, adaptive questioning  
✓ Structured, fair AI evaluation  
✓ Actionable diagnostic feedback  
✓ Multiple practice modes (persona, difficulty, role, JD)  
✓ Downloadable reports for progress tracking  
✓ Security guard against misuse  
✓ Five distinct system prompts implementing different techniques   

### Ready for:

✓ User testing and feedback collection  
✓ Refinement based on real usage data  
✓ Scaling to post-MVP features  
✓ Potential commercialization

---

## File Structure

```
interview-practice-app/
├── rrizwa-AE.1.5-main/
│   └── product_requirement/
│       ├── PRODUCT_REQUIREMENT_DOCUMENT.md  (this file)
│       ├── screen.md
│       └── mock_ups/
├── idea.md
├── suggestion.md
├── follow-up/
│   └── follow-up.md
├── high level/
│   └── high level.md
├── answer sample/
│   └── answer sample.md
├── current question/
│   └── current-question.md
├── json/
│   └── json.md
├── performance/
│   └── (performance notes)
├── screen 8a web view/
│   └── report.md
├── screen 8b pdf/
│   └── report.md
└── production-ready system prompt set.md
```

---

## Implementation Guide: CV-Aware Engine

### Phase 1: Core CV Upload & Extraction (Week 1–2)

#### Deliverables
1. CV upload UI component (Streamlit file uploader)
2. CV text parsing (PDF + plain text)
3. LLM extraction pipeline with enforced JSON schema
4. Session state storage for CV profile

#### Technical Tasks
```python
# 1. Create CV extraction prompt (prompt engineering)
cv_extraction_prompt = """
Extract structured data from the CV.
Output MUST be valid JSON with fields: skills, roles, projects, experience_years
"""

# 2. Implement CV upload handler
@st.sidebar
def cv_upload_section():
    cv_file = st.file_uploader("Upload CV (PDF/TXT)")
    if cv_file:
        cv_text = extract_text(cv_file)
        cv_profile = extract_cv_profile(cv_text)
        st.session_state.cv_profile = cv_profile

# 3. Store in session
st.session_state.cv_profile = {
    "skills": [...],
    "roles": [...],
    "projects": [...],
    "experience_years": X
}
```

---

### Phase 2: Gap Analysis & Question Distribution (Week 2–3)

#### Deliverables
1. CV vs JD comparison algorithm
2. Skill gap identification logic
3. Question type distribution tracker
4. Gap-aware question generation prompt

#### Technical Tasks
```python
# 1. Gap analysis function
def analyze_cv_jd_gap(cv_profile, jd_text):
    cv_skills = extract_keywords(cv_profile['skills'])
    jd_skills = extract_keywords(jd_text)
    gaps = jd_skills - cv_skills
    strengths = cv_skills & jd_skills
    return {"gaps": gaps, "strengths": strengths}

# 2. Question distribution tracker
st.session_state.question_distribution = {
    "cv_based_target": 2,
    "cv_based_asked": 0,
    "jd_based_target": 1.5,
    "jd_based_asked": 0,
    # ... etc
}

# 3. Question generation with type awareness
def generate_question(type, cv_profile, gap_analysis):
    if type == "cv_based":
        prompt += f"Reference this experience from CV: {random.choice(cv_profile['projects'])}"
    elif type == "gap_targeted":
        prompt += f"Focus on this skill gap: {random.choice(gap_analysis['gaps'])}"
    # ... call LLM
```

---

### Phase 3: Problem-Solving Approach Evaluation (Week 3–4)

#### Deliverables
1. Updated evaluation schema (5 dimensions)
2. Reasoning assessment system prompt
3. Problem-Solving Approach scoring logic
4. UI update for Screen 3 (new dimension + assessment section)

#### Technical Tasks
```python
# 1. Update evaluation system prompt
evaluation_prompt = """
Evaluate answer on 5 dimensions:
    [... existing 5 dimensions ...]
5. Problem-Solving Approach (0-10):
   - Logical flow and clarity of reasoning
   - Quality of decision-making explanation
   - Trade-off awareness and articulation
   - Justification of chosen solution

Also provide reasoning_feedback section:
{
  "clarity": "...",
  "alternative_approaches": "...",
  "trade_off_awareness": "..."
}
"""

# 2. Parse and display reasoning assessment
def display_reasoning_feedback(feedback_data):
    st.subheader("Problem-Solving Assessment")
    st.metric("Approach Quality", feedback_data['scores']['problem_solving_approach'])
    st.write("Observations:")
    for obs in feedback_data['reasoning_feedback']['observations']:
        st.write(f"• {obs}")
```

---

### Phase 4: Session Summary & Gap Insights (Week 4)

#### Deliverables
1. Question-level report for each evaluated answer
2. Session-level report with gap analysis
3. Skill recommendations based on gaps
4. Download functionality (PDF/JSON with gap insights)

#### Technical Tasks
```python
# 1. Generate gap-aware session summary
def generate_session_summary(session_data):
    summary = {
        "performance": {...},
        "gap_analysis": {
            "identified_gaps": session_data['gap_analysis']['gaps'],
            "strength_areas": session_data['gap_analysis']['strengths'],
            "recommendation": f"Focus on {top_gap}..."
        },
        "next_steps": [...]
    }
    return summary

# 2. Export to PDF with gap-aware formatting
def export_session_pdf(summary, cv_profile, jd_text):
    # Include gap analysis in report
    pdf.add_section("Skill Gaps Identified", summary['gap_analysis']['gaps'])
    pdf.add_section("Recommended Focus", summary['gap_analysis']['recommendation'])
```

---

### Implementation Checklist

#### Frontend (Streamlit)
- [ ] CV upload component (sidebar)
- [ ] CV profile display (optional)
- [ ] Screen 2: Question type indicator (e.g., "CV-based question")
- [ ] Screen 3: Problem-Solving Assessment section
- [ ] Screen 3: Updated evaluation breakdown (5 dimensions)
- [ ] Screen 6: Gap analysis section in summary
- [ ] Download functionality updated

#### Backend (Python/LLM)
- [ ] CV extraction LLM prompt + enforced JSON schema
- [ ] Gap analysis algorithm (CV vs JD)
- [ ] Question generation with type awareness
- [ ] Question distribution tracking
- [ ] Updated evaluation prompt (5 dimensions + reasoning)
- [ ] Reasoning feedback parsing
- [ ] Session summary with gap insights

#### Testing
- [ ] CV upload with PDF files (various encodings)
- [ ] CV upload with plain text
- [ ] Gap analysis accuracy (test cases)
- [ ] Question distribution validation (40/30/20/10)
- [ ] Reasoning evaluation consistency
- [ ] Session summary report generation
- [ ] Edge case testing (see Edge Cases section)

#### Security
- [ ] Input validation for all user-submitted content
- [ ] Injection detection for off-topic and prompt-injection attempts
- [ ] Session safety controls for CV data and interview state

#### Documentation
- [ ] API documentation for CV extraction
- [ ] Prompt engineering documentation (5 techniques)
- [ ] User guide for CV upload feature
- [ ] Admin guide for gap analysis tuning

---

### Integration Points

#### 1. Session State Structure
```python
st.session_state = {
    "configuration": {..., "cv_profile": {...}},
    "questions": [{..., "type": "cv_based|jd_based|..."}],
    "answers": [...],
    "gap_analysis": {...},
    "question_distribution": {...}
}
```

#### 2. LLM API Calls (Updated)
```python
# Question generation now includes CV context
generate_question(
    role=config['role'],
    cv_profile=st.session_state.cv_profile,  # NEW
    jd=config['jd'],
    gap_analysis=st.session_state.gap_analysis,  # NEW
    question_type="cv_based"  # NEW
)

# Evaluation now returns reasoning feedback
evaluate_answer(
    question=question,
    answer=user_answer,
    cv_context=st.session_state.cv_profile,  # NEW
    reasoning_focus=True  # NEW
)
```

#### 3. Report Generation (Updated)
```python
generate_report(
    session_data=st.session_state,
    include_gap_analysis=True,  # NEW
    include_recommendations=True  # NEW
)
```

---

### Success Criteria for Implementation

**Phase 1 Complete:**
- ✓ User can upload CV (PDF/text)
- ✓ System extracts skills, roles, projects
- ✓ Extracted profile stored in session
- ✓ No crashes or data loss on upload

**Phase 2 Complete:**
- ✓ Gap analysis generates list of missing/weak skills
- ✓ Questions follow 40/30/20/10 distribution
- ✓ Distribution validator confirms balance
- ✓ Gap-targeted follow-ups generated

**Phase 3 Complete:**
- ✓ Problem-Solving Approach dimension scores appear
- ✓ Reasoning feedback section displays correctly
- ✓ Scores reflect decision quality (not just rightness)
- ✓ Users understand "why" feedback

**Phase 4 Complete:**
- ✓ Session summary includes gap analysis
- ✓ Recommendations are actionable
- ✓ PDF/JSON exports include gap insights
- ✓ Users have clear next-steps roadmap

---

### Testing Strategy

#### Unit Tests
- CV extraction: test various formats, encodings
- Gap analysis: validate skill comparison logic
- Question distribution: ensure 40/30/20/10 balance
- Reasoning scoring: validate consistency across test cases

#### Integration Tests
- End-to-end flow: CV upload → question generation → evaluation → report
- Session state: verify persistence and clearing
- API calls: mock OpenRouter responses, validate parsing

#### User Acceptance Tests
- CV upload UX: smooth, clear error messages
- Gap feedback: useful, actionable recommendations
- Reasoning assessment: feels fair and constructive
- Report: clear and actionable

---

### Rollout Plan

**Week 1:** Phase 1 complete; internal testing  
**Week 2:** Phase 2 complete; gap analysis testing  
**Week 3:** Phase 3 complete; reasoning evaluation testing  
**Week 4:** Phase 4 complete; full system testing  
**Week 5:** Beta release to 50 users; feedback collection  
**Week 6:** Refinements based on feedback; production release  

---

## Document Metadata

| Property | Value |
|----------|-------|
| **Document ID** | PRD-2026-04-INTERVIEW-APP-001 |
| **Version** | 1.0 |
| **Last Updated** | April 23, 2026 |
| **Status** | Complete & Validated |
| **Author** | Project Documentation |
| **Reviewers** | Architecture, Product, QA |

---

**End of Document**
