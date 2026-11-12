Create a UI mockup for Screen 1 only.

Show only what the user sees on the screen. Do not include technical notes, state logic, explanations, annotations, or behaviour.

Screen: Interview Setup

Layout:
A single-page app with a left sidebar and a main setup panel.

Left Sidebar (Disabled / Read-only state):
- Title: Interview Practice App

- Section: Configuration
  - Role: —
  - Difficulty: —
  - Persona: —
  - Job Description: —
  - Response Style: —
  - Temperature: —

- Section: Actions
  - Start / Restart (disabled)
  - Exit Session (disabled)

Visual state:
- Slightly faded or greyed out
- No interaction allowed
- Indicates configuration not yet started

--------------------------------------------------

Main Panel:
Title: Interview Setup

Fields:
- Select Role *
  Dropdown: Backend Engineer / Frontend Engineer / etc.

- Select Difficulty *
  Radio: Easy | Medium | Hard

- Select Interviewer Persona *
  Radio: Friendly | Neutral | Strict

- Response Style
  Radio: Concise | Detailed

- Upload CV (Optional)
  [ Upload PDF ]  [ Paste Text ]
  Helper text: Used to personalise questions based on candidate experience

- Job Description (Optional)
  [ Large text area ]
  Helper text: Used to align questions with role requirements

- Model Temperature (Advanced)
  [ Slider: 0.0 ————●———— 1.0 ]
  Default: 0.7

Primary Action:
[ Start Interview ]

--------------------------------------------------

Visual Style:
- Clean, minimal, professional
- Clear spacing between sections
- Sidebar narrower than main panel
- Main panel is the focus
- No popups, no extra screens
- Only this setup screen is visible