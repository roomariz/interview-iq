Create a UI mockup for Screen 4 only.

Show only what the user sees on the screen. Do not include technical notes, behaviour descriptions, state logic, or explanations.

Screen: Improved Answer (Learning Reference)

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
│ Stronger Answer (Example)                                    │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│ At TechCorp, I led a 3-month optimization project for our    │
│ REST API layer, which was causing request latency of 2–3     │
│ seconds. The goal was to reduce latency below 500ms while    │
│ maintaining code maintainability.                            │
│                                                              │
│ I took three approaches:                                     │
│ 1. Profiled the API to identify bottlenecks (database        │
│    queries and serialization)                                │
│ 2. Implemented caching (Redis) and async processing          │
│ 3. Optimized database queries with better indexing           │
│                                                              │
│ Results: Reduced latency from 2000ms to 150ms (13x           │
│ improvement), reduced server costs by 40%, and improved      │
│ user satisfaction (measured by response time complaints).    │
│                                                              │
│ Trade-offs: Added operational complexity with Redis and      │
│ required monitoring overhead, but ROI was clear.             │
│                                                              │
│ [ Next Question ]   [ Back to Feedback ]                     │
│                                                              │
└──────────────────────────────────────────────────────────────┘

--------------------------------------------------

Visual Style:
- Clean, structured, professional
- Clear separation between question, user answer, and improved answer
- Read-only content presentation
- Emphasis on readability and learning
- Sidebar remains static and narrower than main panel
- No popups, no overlays, no additional screens
- Only this screen is shown
