## User Interface & Screens

This document defines the screen structure for the full phased product vision. Phase 1 covers the base interview loop; later phases add personalisation and advanced reporting.

## Screen 0: Welcome (Entry Screen)

**Purpose:** Provide a clear entry point before configuration begins, set expectations, and guide the user into the setup flow.

---

### Layout

```
┌───────────────────────────────────────────────────────────────┐
│ Interview Practice App                                        │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│ Prepare for technical and behavioural interviews through      │
│ structured, adaptive practice sessions.                       │
│                                                               │
│ What you can expect:                                          │
│ • Role-specific interview questions                           │
│ • Real-time evaluation and feedback                           │
│ • Follow-up questions based on your responses                 │
│ • Session summary with actionable insights                    │
│                                                               │
│                                                               │
│ [ Start Setup ]                                               │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

### Behaviour

* This is the default entry screen (`current_screen = "welcome"`)
* No configuration is required at this stage
* Clicking **Start Setup** transitions to Screen 1 (Setup)

---

### State Transition

```plaintext
Welcome → Setup
  trigger: Start Setup clicked AND no active session

Welcome → Resume Flow
  trigger: Resume selected
```

---

### State Initialisation

```python id="welcome_state"
session_state = {
  "current_screen": "welcome",
  "session_complete": False,
  "has_active_session": False,
}
```

### Entry Guard Logic

If session already exists:

- Show:
  [ Resume Session ]
  [ Start New Session ]

Resume:
  → return to last known screen

Start New:
  → clear all session state
  → proceed to setup

---

### Session Reset Rule

On entering Welcome:

- Clear:
  questions, answers, evaluations, gap_analysis

- Reset:
  question_index = 1
  follow_up_count = 0

---

### Interaction Notes

* No sidebar configuration is active at this stage
* Sidebar may be hidden or shown in a disabled/read-only state
* No session data (questions, answers, evaluation) is initialised yet
* Ensures a clean separation between entry and configuration phases

### UX Enhancements
- Estimated session duration: 15–20 minutes
- Note: "You will configure role, difficulty, and preferences next"

---

### Sidebar Behaviour 

- Hidden OR disabled in welcome state
- No configuration visible
- Activated only on setup screen

---

## Design Rationale

* Removes cognitive load by avoiding immediate configuration
* Sets clear expectations before interaction begins
* Provides a controlled starting point for state-driven navigation
* Improves onboarding and usability, particularly for first-time users

---

### Screen Architecture

The application is a **single-page, state-driven interface** with a persistent sidebar and dynamic main panel.

```
┌───────────────────────┬──────────────────────────────────────────┐
│   Sidebar (Persistent)│         Main Panel (Dynamic)             │
│                       │                                          │
│ Configuration         │  Screen 1: Setup                         │
│ • Role                │  Screen 2: Question and Answer           │
│ • Difficulty          │  Screen 3: Feedback and Evaluation       │
│ • Persona             │  Screen 4: Improved Answer               │
│ • Job Description     │  Screen 5: Follow-up or New Question     │
│ • Response Style      │  Screen 6: Session Summary               │
│ • Temperature         │                                          │
│                       │  Question loop operates across           │
│ Actions               │  Screens 2 to 5                          │
│ • Start / Restart     │                                          │
│ • Exit Session        │                                          │
└───────────────────────┴──────────────────────────────────────────┘
```

#### Architectural Control

##### 1. State Model (Explicit)

```
session_state = {
  "current_screen": "setup|question|feedback|improved_answer|follow_up_decision|summary",
  "question_index": int,          # 1–5 (base questions only)
  "follow_up_count": int,         # 0–3 (per base question)
  "current_question_id": str,
  "is_follow_up": bool,
  "session_complete": bool
}
```

###### Clarification:

- question_index tracks base questions only
- follow_up_count is scoped to the current base question and resets on transition

##### 2. Deterministic Screen Transitions

```
Setup → Question
  trigger: Start selected AND configuration valid

Question → Feedback
  trigger: Answer submitted AND validation passed

Feedback → Improved Answer (optional)
  trigger: User selects "Show Example"

Feedback → Follow-up Decision
  trigger: Default post-evaluation transition

Improved Answer → Follow-up Decision
  trigger: User selects "Next"

Follow-up Decision → Question (follow-up)
  trigger: follow_up_count < 3 AND user selects follow-up

Follow-up Decision → Question (new base)
  trigger: user selects new question
  action: increment question_index, reset follow_up_count

Question → Summary
  trigger: question_index > 5 OR session_complete = true

Any Screen → Setup (Restart)
  trigger: restart confirmed
```

##### 3. Loop Control Constraints
- Maximum base questions: 5
- Maximum follow-ups per base question: 3
- follow_up_count resets when a new base question is generated
- Follow-up questions do not increment question_index
- Each base question must complete its follow-up cycle before increment unless skipped by user

##### 4. State Integrity Rules
- current_screen must always match defined enum values
- question_index must remain within 1–5 during active session
- follow_up_count must remain within 0–3
- session_complete = true enforces transition to summary screen
- Invalid state transitions must be blocked and reverted to last valid state

##### 5. Sidebar Behaviour (Clarified)
- Becomes read-only immediately after session start
- Reflects session_state.configuration only
- No runtime mutation permitted except via restart
- Ensures consistency between configuration and evaluation context

##### 6. Restart and Exit Behaviour

```
Restart:

  Clear:
    questions
    answers
    evaluations
    gap_analysis

  Reset:
    question_index = 1
    follow_up_count = 0
    current_screen = "setup"
    session_complete = False

Exit:
  
  Set:
    session_complete = True

  Force transition to summary screen
```

### Screen 1: Setup (Configuration)

**Purpose:** Capture and validate all inputs required to initialise a consistent interview session.

**Phase 1 Fields:** Role, difficulty, persona, response style, temperature.

**Phase 2 Fields:** CV upload, job description input.

**Layout:**
```
┌───────────────────────────────────────────────────────────────┐
│ Interview Setup                                               │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│ Select Role *                                                 │
│ [ Dropdown: Backend Engineer / Frontend Engineer / etc. ]     │
│                                                               │
│ Select Difficulty *                                           │
│ [ Radio: Easy | Medium | Hard ]                               │
│                                                               │
│ Select Interviewer Persona *                                  │
│ [ Radio: Friendly | Neutral | Strict ]                        │
│                                                               │
│ Response Style                                                │
│ [ Radio: Concise | Detailed ]                                 │
│                                                               │
│ Upload CV (Optional)                                          │
│ [ Upload PDF ] or [ Paste Text ]                              │
│ Used to personalise questions based on candidate experience   │
│                                                               │
│ Job Description (Optional)                                    │
│ [ Text Area ]                                                 │
│ Used to align questions with role requirements                │
│                                                               │
│ Model Temperature (Advanced)                                  │
│ [ Slider: 0.0 ————●———— 1.0 ] (Default: 0.7)                  │
│                                                               │
│                                                               │
│ [ Start Interview ]                                           │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

**Behavior:**
- Fields marked with * are mandatory: role, difficulty, persona
- Validation occurs on submission; invalid inputs prevent transition
- Inline error messages are displayed directly beneath the relevant field
- No modal or page interruption is introduced during validation

**Validation Rules:**
- Role: must be selected from predefined list
- Difficulty: exactly one option must be selected
- Persona: exactly one option must be selected
- CV input:
  - Max file size: 2–5 MB
  - Max extracted text: 50,000 characters
  - Reject unsupported formats
  - Fallback to text input if parsing fails

- Job Description:
  - Minimum length: 50 characters (strict)
  - Trim whitespace before validation

- Temperature:
  - Allowed range: 0.0–1.0
  - Default: 0.7
  - Optional: lock to default in production for consistency

**State Initialisation:**
```
session_state = {
  "current_screen": "question",
  "question_index": 1,
  "follow_up_count": 0,
  "is_follow_up": False,
  "session_complete": False,

  "current_question_id": None,

  "questions": [],
  "answers": [],

  "gap_analysis": None,
  "question_distribution": {
    "cv_based_asked": 0,
    "jd_based_asked": 0,
    "behavioral_asked": 0,
    "deep_dive_asked": 0
  },

  "configuration": {
    "role": selected_role,
    "difficulty": selected_difficulty,
    "persona": selected_persona,
    "response_style": selected_style,
    "temperature": selected_temperature,
    "job_description": jd_input,
    "cv_profile": parsed_cv
  }
}
```

**CV Processing Control:**
- CV parsing must complete BEFORE:
  - gap analysis
  - first question generation

- Introduce state:
  cv_processing_status = "pending|complete|failed"

- Block transition to first question until:
  status == complete OR failed (fallback mode)

**Loading State:**
On submission:

- Show inline loading state:
  "Preparing your interview..."

- Steps:
  1. CV parsing
  2. Gap analysis (if JD present)
  3. First question generation

- Transition only after all steps complete

**Interaction Safeguards:**
- Disable "Start Interview" after click (prevent double submission)
- Prevent state overwrite if session already active
- Ensure configuration is immutable post-start

---

### Screen 2: Question & Answer (Main Loop)

**Purpose:** Present question and collect user answer

**Content:**
```
┌──────────────────────────────────────────────────────────────┐
│ Question 1 of 5                                              │
├──────────────────────────────────────────────────────────────┤
│ Role: Backend Engineer | Difficulty: Medium | Persona: Strict│
│ Focus: Performance Optimization                              │
│                                                              │
│ Describe a time you improved system performance under        │
│ constraints. Include the challenge, your approach, and       │
│ measurable results.                                          │
└──────────────────────────────────────────────────────────────┘


┌──────────────────────────────────────────────────────────────┐
│ Your Answer                                                  │
├──────────────────────────────────────────────────────────────┤
│ [ Large text area (min 50, max 2000 chars) ]                │
│ ________________________________________________________      │
│ ________________________________________________________      │
│ ________________________________________________________      │
│                                                              │
│ Character count: 0 / 2000                                    │
│                                                              │
│ [ Submit Answer ]  [ Clear ]                                 │
└──────────────────────────────────────────────────────────────┘
```

**Security Guard (if triggered):**
```
┌──────────────────────────────────────────────────────────────┐
│ Your Answer                                                  │
├──────────────────────────────────────────────────────────────┤
│ ⚠ This application supports interview preparation only.      │
│ Please provide a relevant interview response.                │
│                                                              │
│ [ Large text area (min 50, max 2000 chars) ]                │
│ ________________________________________________________      │
│                                                              │
│ [ Submit Answer ]  [ Clear ]                                 │
└──────────────────────────────────────────────────────────────┘
```

**Behavior:**
- Warning appears inline in input section
- Warning disappears automatically when input becomes valid
- No modal or page reload
- Submit disabled until input valid and minimum characters reached

---

### Screen 3: Feedback (Post-Answer Evaluation)

**Purpose:** Display AI evaluation and diagnostic feedback

**Content:**
```
┌──────────────────────────────────────────────────────────────┐
│ Your Question                                                │
├──────────────────────────────────────────────────────────────┤
│ Describe a time you improved system performance...           │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│ Your Answer (submitted)                                      │
├──────────────────────────────────────────────────────────────┤
│ In my previous role at TechCorp, I led optimization of      │
│ our API layer. We reduced latency from 2s to 200ms...       │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│ Diagnostic Feedback                                          │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│ Overall Outcome: ✓ PASS                                     │
│                                                              │
│ Evaluation Breakdown                                         │
│ ┌──────────────────────────────────────────────────────┐    │
│ │ Relevance        ███████░░░ 7/10                     │    │
│ │ Structure        ████░░░░░░ 4/10                     │    │
│ │ Specificity      ████░░░░░░ 4/10                     │    │
│ │ Communication    ███████░░░ 7/10                     │    │
│ │ Problem-Solving  █████░░░░░ 5/10                     │    │
│ │ Approach                                             │    │
│ └──────────────────────────────────────────────────────┘    │
│                                                              │
│ What the Interviewer is Evaluating:                         │
│ • Problem-solving clarity and approach                      │
│ • Ownership and impact                                      │
│ • Communication and structure (STAR)                        │
│ • Technical depth and trade-offs                            │
│                                                              │
│ Problem-Solving Assessment                                  │
│ ┌──────────────────────────────────────────────────────┐    │
│ │ Approach Quality: 5/10                               │    │
│ │                                                      │    │
│ │ Observations:                                        │    │
│ │ • Solution is correct but reasoning is implicit      │    │
│ │ • Limited discussion of alternative approaches      │    │
│ │ • Trade-offs not clearly articulated                │    │
│ │                                                      │    │
│ │ How to Improve:                                      │    │
│ │ • Explain why you chose this solution over others   │    │
│ │ • Mention at least one alternative and why it was  │    │
│ │   rejected                                           │    │
│ │ • Link decisions to constraints (perf, cost, etc.)   │    │
│ └──────────────────────────────────────────────────────┘    │
│                                                              │
│ Key Issues:                                                 │
│ • Missing measurable impact (what does 10x mean?)           │
│ • Vague on technical approach                               │
│                                                              │
│ How to Improve:                                             │
│ • Add specific metrics (latency, throughput, cost)          │
│ • Explain technical decisions and trade-offs                │
│ • Use STAR: Situation, Task, Action, Result                │
│                                                              │
│ [ Show Example Answer ]  [ View Technical Breakdown ▼ ]     │
│ [ Download Evaluation Report ]                              │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

**If "View Technical Breakdown" clicked (expands inline):**
```
Technical Evaluation (JSON)

{
  "overall_decision": "pass",
  "scores": {
    "relevance": 7,
    "structure": 4,
    "specificity": 4,
    "communication": 7,
    "problem_solving_approach": 5
  },
  "labels": {
    "relevance": "Addresses the question directly",
    "structure": "Needs clearer STAR organization",
    "specificity": "Lacks measurable outcomes",
    "communication": "Clear and easy to follow",
    "problem_solving_approach": "Solution is correct, but reasoning is implicit"
  },
  "key_issues": [
    "Missing specific metrics for improvement",
    "Vague on technical approach",
    "Limited explanation of why this solution was chosen"
  ],
  "improvements": [
    "Add quantifiable results (10x latency reduction)",
    "Explain technical decisions and trade-offs",
    "Discuss alternative approaches and why they were rejected"
  ],
  "reasoning_feedback": {
    "clarity": "Solution is valid but reasoning behind choosing it is not clearly explained",
    "alternative_approaches": "Did not mention considered alternatives",
    "trade_off_awareness": "Trade-offs mentioned but not thoroughly articulated"
  }
}
```

**Behavior:**
- Original question and answer remain visible
- Answer is read-only
- Feedback is interactive (expandable sections)
- Report download available

---

### Screen 4: Improved Answer (Learning Reference)

**Purpose:** Show better answer approach for learning

**Content:**
```
[Same: Question card, Answer (read-only)]

┌──────────────────────────────────────────────────────────────┐
│ Stronger Answer (Example)                                    │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│ At TechCorp, I led a 3-month optimization project for our   │
│ REST API layer, which was causing request latency of 2–3    │
│ seconds. The goal was to reduce latency below 500ms while   │
│ maintaining code maintainability.                            │
│                                                              │
│ I took three approaches:                                     │
│ 1. Profiled the API to identify bottlenecks (database       │
│    queries and serialization)                                │
│ 2. Implemented caching (Redis) and async processing          │
│ 3. Optimized database queries with better indexing           │
│                                                              │
│ Results: Reduced latency from 2000ms to 150ms (13x          │
│ improvement), reduced server costs by 40%, and improved      │
│ user satisfaction (measured by response time complaints).    │
│                                                              │
│ Trade-offs: Added operational complexity with Redis and      │
│ required monitoring overhead, but ROI was clear.             │
│                                                              │
│ [ Next Question ]  or  [ Back to Feedback ]                  │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

**Behavior:**
- Serves as a learning reference
- User can review then continue to follow-up or next question
- Not presented as "the only right answer" but as "a stronger approach"

---

### Screen 5: Follow-up or New Question (Loop Decision)

**Purpose:** Decide: Continue with follow-up or start new base question?

**Content:**
```
┌──────────────────────────────────────────────────────────────┐
│ Continue Learning                                            │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│ Would you like a follow-up question on this topic, or a new │
│ question?                                                    │
│                                                              │
│ [ Follow-up Question ]  [ New Base Question ]  [ Exit ]      │
│                                                              │
│ (If Follow-up selected, shows new question in same format)   │
│ (If New Question selected, returns to Screen 2 with Q2)      │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

**Note:** In implementation, this may be implicit (automatic follow-up unless user requests new question). Follow-up questions appear as "Question 1.5 of 5" in the UI.

---

### Screen 6: Session Summary (End of Session)

**Purpose:** Provide aggregated insights and completion report

**Content:**
```
┌──────────────────────────────────────────────────────────────┐
│ Interview Session Complete!                                 │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│ Overall Performance: 68% (Needs Improvement)                │
│                                                              │
│ Questions Completed: 5                                       │
│ Session Duration: 18 minutes                                 │
│                                                              │
│ ─────────────────────────────────────────────────────────────│
│ Performance Breakdown                                        │
│                                                              │
│ Average Scores (across all questions):                       │
│ Relevance        ███████░░░ 7/10 (Good)                     │
│ Structure        ████░░░░░░ 4.4/10 (Needs Work)             │
│ Specificity      ████░░░░░░ 4.2/10 (Needs Work)             │
│ Communication    ███████░░░ 6.8/10 (Good)                   │
│ Problem-Solving Approach █████░░░░░ 5.0/10 (Needs Work)      │
│                                                              │
│ ─────────────────────────────────────────────────────────────│
│ Skill Gap Analysis                                           │
│ • Missing skills (from CV vs JD): Distributed Systems,      │
│   Cloud Architecture                                         │
│ • Strength areas: Backend Development, Performance          │
│   Optimization                                               │
│ • Recommended focus: Practice distributed systems scenarios │
│                                                              │
│ ─────────────────────────────────────────────────────────────│
│ Key Strengths:                                               │
│ • Clear communication of ideas                              │
│ • Relevant examples from experience                          │
│ • Good understanding of domain challenges                    │
│                                                              │
│ Areas for Improvement:                                       │
│ • Add specific metrics and measurable outcomes               │
│ • Structure answers using STAR format                        │
│ • Explain technical trade-offs                              │
│ • Provide more depth on complex topics                       │
│                                                              │
│ ─────────────────────────────────────────────────────────────│
│ Common Issues Across Questions:                              │
│ • Missing quantifiable results (3/5 questions)               │
│ • Weak on trade-off discussion (4/5 questions)               │
│ • Could improve organization (4/5 questions)                 │
│                                                              │
│ ─────────────────────────────────────────────────────────────│
│ Recommended Next Steps:                                      │
│ 1. Practice STAR framework (Situation, Task, Action,Result)  │
│ 2. Prepare specific metrics for key projects                 │
│ 3. Practice follow-up questions on technical trade-offs      │
│ 4. Try again at HARD difficulty level                        │
│                                                              │
│ [ Download Session Summary ]  [ View Full Report ]           │
│ [ Start New Session ]  [ Exit ]                              │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

**Expandable "View Full Report":**
```
Full Interview Session Report

Session Metadata:
• Date: 2026-04-23, 14:30–14:48
• Role: Backend Engineer
• Difficulty: Medium
• Persona: Strict
• Response Style: Detailed
• CV Context: Senior Backend Engineer, API optimization, Go/Python
• Gap Analysis: Missing distributed systems and cloud architecture depth

Questions Attempted:
1. "Describe a time you improved system performance..."
   - Your Score: PASS (Overall 6.8/10)
   - Feedback: Good communication, needs metrics

2. "What trade-offs did you consider?"
   - Your Score: BORDERLINE (Overall 5.8/10)
   - Feedback: Good thinking, needs structure

... [and so on for Q3-Q5]

Overall Summary:
• Best Performance: Q1 (Communication)
• Weakest Performance: Q3 (Specificity)
• Improvement Trend: Slight improvement Q1→Q5
• Estimated Readiness: 68% (Needs more practice)
```

**Behavior:**
- User can download as PDF or JSON
- Report includes all metrics, scores, and recommendations
- Persistent link to download again later (if persistent DB available in future)

---

### Navigation Flow

```
                        ┌─────────────┐
                        │   Setup     │
                        │ Screen 1    │
                        └──────┬──────┘
                               │ [Start]
                               ▼
                        ┌─────────────┐
                        │  Question   │
                        │ Screen 2    │
                        └──────┬──────┘
                               │ [Submit]
                               ▼
                        ┌─────────────┐
                        │  Feedback   │
                        │ Screen 3    │
                        └──────┬──────┘
                               │ [Show Example]
                               ▼
                        ┌─────────────┐
                        │   Improved  │
                        │ Screen 4    │
                        └──────┬──────┘
                               │ [Next]
                               ▼
                   ┌───────────────────────┐
                   │  Follow-up Decision?  │
                   │  [Follow-up] [New]    │
                   └───┬─────────────────┬─┘
                       │                 │
         [Follow-up]   │                 │ [New Question]
                  ┌────┘                 └──────┐
                  │                             │
                  ▼                             ▼
            [Follow-up Q] ──→ [Screen 2] ←── [Base Q2]
                             (Loop repeats)
                                   │
                             (After Q5)
                                   │
                                   ▼
                            ┌──────────────┐
                            │   Summary    │
                            │ Screen 6     │
                            └──────┬───────┘
                                   │
                        [Download / New Session / Exit]
```

![Navigation Flow](./architecture_&_flow_diagram/Navigation%20Flow.png)
