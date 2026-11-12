Note: The features listed below represent the full phased product vision. Phase 1 is the MVP, with later phases adding personalisation, advanced evaluation, and growth capabilities.

## Features

### Phase 1 MVP

#### 1. Welcome and Setup Flow
- **Description:** Provides the entry screen, interview setup screen, and clear session start flow
- **Value:** Simple onboarding and deterministic navigation
- **Technical:** Streamlit layout and session state control

#### 2. Interview Simulation Engine
- **Description:** Generates contextually relevant interview questions based on role, difficulty, persona, and response style
- **Value:** Realistic practice environment
- **Technical:** OpenRouter API with prompt engineering

#### 3. Answer Validation and Security Guard
- **Description:** Validates answer length, relevance, and basic injection patterns before submission
- **Value:** Maintains data quality and prevents misuse
- **Technical:** Relevance checks, length checks, and prompt-injection filtering

#### 4. Structured AI Evaluation
- **Description:** Scores answers on relevance, structure, specificity, communication, and problem-solving approach
- **Value:** Objective, fair, consistent feedback
- **Technical:** Structured JSON output with five evaluation dimensions

#### 5. Diagnostic Feedback
- **Description:** Shows strengths, key issues, and improvement guidance after each answer
- **Value:** Actionable coaching feedback
- **Technical:** Response parsing and feedback rendering

#### 6. Improved Answer View
- **Description:** Presents a stronger example answer for learning reference
- **Value:** Helps users understand how to improve
- **Technical:** Template-based or model-generated reference output

#### 7. Follow-up / New Question Decision
- **Description:** Lets the user continue with a follow-up or move to the next base question
- **Value:** Keeps the interview flow controlled and predictable
- **Technical:** Session-state-driven question loop

#### 8. Session Summary
- **Description:** Summarises the interview session at the end of five base questions
- **Value:** Clear end-of-session review
- **Technical:** Aggregated session data display

#### 9. Basic Report Download
- **Description:** Allows the user to download a basic session report
- **Value:** Simple record of the session outcome
- **Technical:** Lightweight PDF or JSON export

### Phase 2 Personalisation

#### 10. CV-Aware Personalisation
- **Description:** Upload a CV and extract structured profile data for tailored questions and feedback
- **Value:** More realistic, candidate-specific practice
- **Technical:** CV extraction with structured JSON output

#### 11. Job Description Integration
- **Description:** Add a job description to tailor practice to the target role
- **Value:** More relevant preparation for real applications
- **Technical:** JD included in question-generation context

#### 12. CV/JD Gap Analysis
- **Description:** Compares CV and job description to identify missing or weak coverage areas
- **Value:** Clear preparation roadmap
- **Technical:** Skill comparison and gap identification logic

#### 13. Weighted Question Distribution
- **Description:** Balances question types across the session for realistic coverage
- **Value:** Prevents bias towards one question type
- **Technical:** Question type tracking and distribution logic

#### 14. Gap-Targeted Follow-Ups
- **Description:** Generates follow-up questions based on identified CV/JD gaps
- **Value:** Focuses practice on weakest areas
- **Technical:** Gap-aware follow-up generation

### Phase 3 Advanced Evaluation

#### 15. Advanced Reasoning Assessment
- **Description:** Evaluates the reasoning behind answers, including decision clarity and trade-offs
- **Value:** Teaches users to explain how they think
- **Technical:** Reasoning-focused evaluation prompts

#### 16. Technical JSON Breakdown
- **Description:** Exposes structured evaluation data for deeper review
- **Value:** Transparent diagnostics for advanced users
- **Technical:** JSON response viewer and schema rendering

#### 17. Advanced Reports
- **Description:** Generates richer question-level and session-level reports
- **Value:** More detailed review and retention
- **Technical:** Extended PDF and JSON report formats

#### 18. Richer Diagnostic Outputs
- **Description:** Adds deeper reasoning, trade-off, and improvement guidance
- **Value:** Stronger coaching and clearer next steps
- **Technical:** Expanded evaluation payloads

### Phase 4 Growth

#### 19. User Accounts
- **Description:** Supports named user accounts
- **Value:** Personalised experience across visits
- **Technical:** Authentication and identity management

#### 20. Persistent Database
- **Description:** Stores sessions and user data across visits
- **Value:** Long-term tracking and history
- **Technical:** Persistent storage layer

#### 21. Analytics Dashboard
- **Description:** Shows performance trends and progress over time
- **Value:** Better insight into improvement patterns
- **Technical:** Aggregated analytics views

#### 22. Model Selection
- **Description:** Lets the user choose from allowed models
- **Value:** More control for advanced users
- **Technical:** Model selector and configuration state

#### 23. Multi-Session Tracking
- **Description:** Tracks progress across multiple practice sessions
- **Value:** Longitudinal improvement insights
- **Technical:** Session history and trend aggregation

#### 24. Team Features
- **Description:** Supports organisations, cohorts, and shared administration
- **Value:** Enables group usage and licensing
- **Technical:** Team-level roles and shared reporting

---
