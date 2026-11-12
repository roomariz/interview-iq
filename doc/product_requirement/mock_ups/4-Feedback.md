Create a UI mockup for Screen 3 only.

Show only what the user sees on the screen. Do not include technical notes, behaviour descriptions, state logic, or explanations.

Screen: Feedback (Post-Answer Evaluation)

Layout:
A single-page app with a left sidebar and a main content panel.

--------------------------------------------------

Left Sidebar (Read-only):
- Title: Interview Practice App

- Section: Configuration
  - Role: Backend Engineer
  - Difficulty: Medium
  - Persona: Strict
  - Response Style: Detailed
  - Job Description: —
  - CV: —
  - Temperature: 0.7

- Section: Actions
  - Restart
  - Exit Session

--------------------------------------------------

Main Panel:

┌──────────────────────────────────────────────────────────────┐
│ Your Question                                                │
├──────────────────────────────────────────────────────────────┤
│ Describe a time you improved system performance...           │
└──────────────────────────────────────────────────────────────┘


┌──────────────────────────────────────────────────────────────┐
│ Your Answer (submitted)                                      │
├──────────────────────────────────────────────────────────────┤
│ In my previous role at TechCorp, I led optimization of       │
│ our API layer. We reduced latency from 2s to 200ms...        │
└──────────────────────────────────────────────────────────────┘


┌──────────────────────────────────────────────────────────────┐
│ Diagnostic Feedback                                          │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│ Overall Outcome: ✓ PASS                                      │
│                                                              │
│ Evaluation Breakdown                                         │
│ ┌──────────────────────────────────────────────────────┐     │
│ │ Relevance        ███████░░░ 7/10                     │     │
│ │ Structure        ████░░░░░░ 4/10                     │     │
│ │ Specificity      ████░░░░░░ 4/10                     │     │
│ │ Communication    ███████░░░ 7/10                     │     │
│ │ Problem-Solving  █████░░░░░ 5/10                     │     │
│ │ Approach                                             │     │
│ └──────────────────────────────────────────────────────┘     │
│                                                              │
│ What the Interviewer is Evaluating:                          │
│ • Problem-solving clarity and approach                       │
│ • Ownership and impact                                       │
│ • Communication and structure (STAR)                         │
│ • Technical depth and trade-offs                             │
│                                                              │
│ Problem-Solving Assessment                                   │
│ ┌──────────────────────────────────────────────────────┐     │
│ │ Approach Quality: 5/10                               │     │
│ │                                                      │     │
│ │ Observations:                                        │     │
│ │ • Solution is correct but reasoning is implicit      │     │
│ │ • Limited discussion of alternative approaches       │     │
│ │ • Trade-offs not clearly articulated                 │     │
│ │                                                      │     │
│ │ How to Improve:                                      │     │
│ │ • Explain why you chose this solution over others    │     │
│ │ • Mention at least one alternative and why it was   │     │
│ │   rejected                                           │     │
│ │ • Link decisions to constraints (perf, cost, etc.)   │     │
│ └──────────────────────────────────────────────────────┘     │
│                                                              │
│ Key Issues:                                                  │
│ • Missing measurable impact (what does 10x mean?)            │
│ • Vague on technical approach                                │
│                                                              │
│ How to Improve:                                              │
│ • Add specific metrics (latency, throughput, cost)           │
│ • Explain technical decisions and trade-offs                 │
│ • Use STAR: Situation, Task, Action, Result                  │
│                                                              │
│ [ Show Example Answer ]   [ View Technical Breakdown ▼ ]      │
│ [ Download Evaluation Report ]                               │
│                                                              │
└──────────────────────────────────────────────────────────────┘


--------------------------------------------------

Expanded Section (if "View Technical Breakdown" opened):

┌──────────────────────────────────────────────────────────────┐
│ Technical Evaluation (JSON)                                  │
├──────────────────────────────────────────────────────────────┤
│ {                                                            │
│   "overall_decision": "pass",                                │
│   "scores": {                                                │
│     "relevance": 7,                                          │
│     "structure": 4,                                          │
│     "specificity": 4,                                        │
│     "communication": 7,                                      │
│     "problem_solving_approach": 5                            │
│   },                                                         │
│   "labels": {                                                │
│     "relevance": "Addresses the question directly",          │
│     "structure": "Needs clearer STAR organization",          │
│     "specificity": "Lacks measurable outcomes",              │
│     "communication": "Clear and easy to follow",             │
│     "problem_solving_approach": "Solution is correct, but    │
│     reasoning is implicit"                                   │
│   },                                                         │
│   "key_issues": [                                            │
│     "Missing specific metrics for improvement",              │
│     "Vague on technical approach",                           │
│     "Limited explanation of why this solution was chosen"    │
│   ],                                                         │
│   "improvements": [                                          │
│     "Add quantifiable results (10x latency reduction)",      │
│     "Explain technical decisions and trade-offs",            │
│     "Discuss alternative approaches and why they were        │
│      rejected"                                               │
│   ]                                                          │
│ }                                                            │
└──────────────────────────────────────────────────────────────┘

--------------------------------------------------

Visual Style:
- Clean, structured, professional
- Clear hierarchy between sections
- Read-only answer display
- Feedback sections clearly separated
- Sidebar remains static and narrower than main panel
- No popups, no overlays, no additional screens
- Only this screen is shown
