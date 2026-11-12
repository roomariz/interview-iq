Act as a senior product designer and UI/UX architect.

Your task is to generate a high-fidelity UI mockup for a web application screen.

Screen Name: "Welcome (Entry Screen)"
Application: Interview Practice App (AI-powered interview preparation platform)

Context:
This is the first screen in a single-page, state-driven application. It appears before any configuration is performed.

The UI must reflect:
- Clarity
- Minimal cognitive load
- Strong onboarding guidance
- Deterministic navigation (no ambiguity in actions)

----------------------------------------

LAYOUT REQUIREMENTS

Create a clean, centred layout with the following structure:

1. Header Section:
- Title: "Interview Practice App"
- Positioned at the top
- Clear, professional styling

2. Main Content (Centered):
- Short description:
  "Prepare for technical and behavioural interviews through structured, adaptive practice sessions."

- Section heading:
  "What you can expect:"

- Bullet points:
  • Role-specific interview questions  
  • Real-time evaluation and feedback  
  • Follow-up questions based on your responses  
  • Session summary with actionable insights  

3. CTA (Primary Action):
- Button: "Start Setup"
- Prominent and centred
- Only primary action on screen

4. Optional UX Enhancements:
- Small note below CTA:
  "Estimated time: 15–20 minutes"
- Helper text:
  "You will configure role, difficulty, and preferences next"

----------------------------------------

BEHAVIOUR REQUIREMENTS

- This screen represents:
  current_screen = "welcome"

- No input fields or configuration visible
- No session data initialised

- On click:
  "Start Setup" → transitions to Setup screen

----------------------------------------

STATE MANAGEMENT

Initial session state:

session_state = {
  "current_screen": "welcome",
  "session_complete": false,
  "has_active_session": false
}

----------------------------------------

ADVANCED LOGIC (IMPORTANT)

If an active session exists:

Display two buttons instead of one:

- "Resume Session"
- "Start New Session"

Behaviour:

Resume Session:
→ Return to last known screen

Start New Session:
→ Clear all session data:
   questions, answers, evaluations, gap_analysis
→ Reset:
   question_index = 1
   follow_up_count = 0
→ Navigate to Setup

----------------------------------------

SIDEBAR RULES

- Sidebar must be:
  - Hidden OR
  - Visible but disabled (read-only)

- No configuration options shown

----------------------------------------

DESIGN CONSTRAINTS

- Minimalist and distraction-free
- No secondary actions beyond defined ones
- High readability and spacing
- Professional tone (no playful UI)
- Accessible (WCAG-friendly contrast and layout)

----------------------------------------

OUTPUT FORMAT

Provide:

1. Visual mockup (ASCII or structured layout)
2. Component breakdown
3. Interaction flow
4. State transition explanation

Ensure the design strictly follows a deterministic, state-driven architecture.
Do not introduce new features or flows beyond what is defined.





