## Product Requirements

This document defines the full phased product vision. Phase 1 is the MVP, with later phases extending the same product without changing the base structure.

### Functional Requirements

#### 1. User Setup and Configuration

**FR-1.1: Role Selection**
- User selects target role (e.g. Backend Engineer, Frontend Engineer, Product Manager, Data Engineer)
- System uses role-specific context to dynamically generate interview questions via LLM (no static question bank)
- Selected role persists for the duration of the session

**FR-1.2: Interview Difficulty Selection**
- User selects difficulty level: Easy, Medium, or Hard
- Selected difficulty defines baseline question complexity and scoring thresholds
- Difficulty is maintained across all questions and follow-ups within the session

**FR-1.3: Interviewer Persona Selection**
- User selects interviewer persona: Friendly, Neutral, or Strict
- Persona influences question style and feedback tone
- Persona remains consistent throughout the session

**FR-1.4: Job Description (Phase 2)**
- User may upload or paste a job description
- System uses the job description to contextualise question generation and evaluation
- If no job description is provided, the system defaults to role-based context

**FR-1.5: Response Style Selection**
- User selects response style: Concise or Detailed
- System adjusts evaluation criteria and expected response depth accordingly
- Feedback is aligned with the selected response style

**FR-1.6: Model Configuration**
- User may adjust model temperature (creativity/randomness), where exposed
- Default temperature is set to 0.7 (balanced output)
- Configuration changes apply to subsequent sessions only

**FR-1.7: CV Upload and Processing (Phase 2)**
- User may upload a CV (PDF) or provide content as plain text
- System extracts structured data using LLM into a defined JSON schema, including:
  - Skills (technical and soft)
  - Roles and titles (including seniority and duration where available)
  - Projects and accomplishments (including measurable impact and ownership)
  - Technologies and tools (linked to projects where possible)
  - Certifications (e.g. AWS, Azure, Scrum)
  - Education (optional; degrees, institutions, relevant coursework)

- Extraction is enforced as structured JSON output for downstream consistency
- Extracted profile is stored in session state only (no persistent storage)
- CV data is used exclusively for:
  - question generation
  - answer evaluation
  - CV–JD gap analysis

- If no CV is provided, the system defaults to role and job description context
- CV upload is optional and does not block the interview flow
- User is provided with an option to review or edit extracted CV data before starting the interview

---

#### 2. Interview Flow and Question Generation

**FR-2.1: Initial Question Generation**
- Questions are generated dynamically using the LLM (no static question bank), based on:
  - role
  - selected difficulty
  - interviewer persona
  - job description (if provided)
  - CV profile (if provided)

- Questions are contextually relevant and personalised to the user’s experience and target role
- Questions are displayed in the "Current Question" panel
- Where a CV is provided, questions reference the user’s background where appropriate

- The selected difficulty level (Easy, Medium, Hard) defines the baseline complexity, depth, and expected answer quality for the session
- Difficulty is internally modelled as a continuous scale rather than fixed levels

- Within a session, question complexity is adaptively adjusted based on user performance:
  - Initial questions begin at the lower bound of the selected difficulty
  - Complexity increases in depth, ambiguity, and required reasoning where strong performance is demonstrated
  - Where performance is weaker, complexity is maintained or slightly reduced to reinforce core concepts
      - The system maintains internal difficulty scoring per question to ensure smooth progression rather than abrupt shifts in complexity

**FR-2.2: Question Display**
- Question display includes:
  - role
  - difficulty level
  - interviewer persona
  - defined focus area

- Questions provide clear context, expectations, and scope of response
- Where applicable, questions reference CV or job description context
- Questions are interview-realistic and scenario-based, focusing on applied, experience-driven situations
- Purely theoretical or definition-based prompts are avoided

**FR-2.3: Follow-Up Question Generation (Phase 2)**
- After answer submission, the system analyses the response and generates a follow-up question

- Follow-up questions are adaptively generated to:
  - address identified gaps (e.g. missing detail, weak reasoning, CV–JD skill gaps)
  - probe deeper into demonstrated strengths

- Follow-up appears as the next question within the same UI (no screen transition)
- Follow-up questions maintain continuity with the prior context and do not reset topic unless transitioning to a new base question

- A maximum of 3 follow-up questions may be generated per base question
- Once the limit is reached, the system transitions to a new base question

**FR-2.4: Question Loop Management**
- A session consists of 5 base questions
- Each base question may include up to 3 follow-up questions
- Follow-up questions do not count towards the total of 5 base questions

- At each step, the user may:
  - accept a follow-up question, or
  - proceed to the next base question

- The session ends when:
  - all 5 base questions are completed, or
  - the user chooses to exit

**FR-2.5: Context-Enriched Question Generation (Weighted Distribution, Phase 2)**
- Question type distribution is enforced across each 5-question session:

  - 40% CV-based (experience-specific, referencing the user’s background)
  - 30% JD-based (aligned to role expectations and job description)
  - 20% behavioural (communication, teamwork, culture fit)
  - 10% deep-dive (advanced scenarios, edge cases, and trade-offs)

- Distribution applies to base questions only; follow-up questions are excluded

- The system dynamically tracks and adjusts question selection to meet distribution targets across the full session (not per question)

- Where exact percentage mapping is not possible, the system applies the closest proportional distribution across 5 base questions

- If no CV is provided, the CV-based allocation is redistributed:
  - 40% → JD-based (20%) and behavioural (20%)

---

#### 3. Answer Collection and Validation

**FR-3.1: Answer Submission**
- Users enter responses in a large text input area
- Minimum length: 50 characters; maximum length: 2,000 characters
- Input is validated in real time and on submission to enforce length and quality constraints
- Submission remains disabled until minimum length and validation criteria are satisfied
- Character count is displayed and updates dynamically

- Validated responses are passed to the evaluation engine with full contextual data:
  - question
  - role
  - difficulty
  - persona
  - CV profile (if available)
  - job description (if available)
      - Partial answers are preserved locally to prevent data loss during interruption or refresh

**FR-3.2: Security Guard (Input Validation)**
- User input is evaluated for relevance to the current question in real time and at submission

- Off-topic or irrelevant responses are detected using a hybrid approach:
  - lightweight keyword and pattern matching for immediate filtering
  - LLM-based semantic classification against the question context

- Where input is identified as irrelevant, an inline warning is displayed:
  "This application supports interview preparation only. Please provide a relevant response."

- The warning:
  - is non-blocking during typing
  - prevents submission while the response remains invalid
  - is automatically removed once relevance criteria are met

- Validation operates fully inline within the answer component, with no modal, redirect, or page interruption

- Repeated invalid submissions trigger progressively stronger guidance, including examples aligned to the current question

**FR-3.3: Prompt Injection Prevention**
- The system enforces input validation and security controls at submission stage

- Submission is blocked where responses:
  - contain prompt injection patterns (e.g. attempts to override system instructions)
  - are empty or below the minimum threshold
  - exhibit characteristics of spam or non-meaningful content (e.g. repetition, random strings, high-entropy text)

- Prompt injection detection uses:
  - keyword and pattern-based filtering (e.g. "ignore instructions", "override system")
  - LLM-based classification for ambiguous cases

- Spam or non-meaningful content detection uses heuristic checks, including:
  - entropy or randomness scoring
  - repetition and structural pattern analysis

- Where a response is blocked:
  - submission is prevented
  - a clear inline validation message explains the issue
  - the user is prompted to revise the response without disrupting the session flow

- Repeated injection attempts may trigger safeguards, including temporary input restriction or session reset

- All validation and enforcement remains inline within the answer component, with no modal, redirect, or page interruption

**FR-3.4: Answer Context Preservation**
- Once submitted, an answer becomes read-only for the remainder of the session
- Users may copy their submitted response, but editing is not permitted

- The original answer remains persistently visible across:
  - feedback and evaluation screens
  - improved (example) answer views
  - follow-up question interactions

- The system preserves the original response without modification to ensure:
  - accurate comparison against feedback and suggested improvements
  - continuity of context across follow-up questions
  - auditability of the user’s reasoning and communication

---

#### 4. AI-Powered Evaluation & Feedback

**FR-4.1: Structured Evaluation**
- Each response is evaluated across five dimensions:

  - Relevance (0–10): extent to which the response addresses the question
  - Structure (0–10): clarity, organisation, and use of frameworks (e.g. STAR)
  - Specificity (0–10): use of concrete details, examples, and measurable outcomes
  - Communication (0–10): clarity, coherence, and ease of understanding
  - Problem-Solving Approach (0–10): quality of reasoning, decision-making, and justification

**FR-4.2: Scoring and Decision**
- Overall decision weighting prioritises reasoning quality and relevance over surface-level correctness
  - Each dimension is scored on a 0–10 scale:
    - 0–3: Weak  
    - 4–6: Needs improvement  
    - 7–8: Strong  
    - 9–10: Excellent  

- An overall decision is derived:
  - Pass
  - Borderline Pass
  - Fail

- The decision is displayed prominently, supported by clear reasoning

**FR-4.3: Diagnostic Feedback**
- The system provides structured feedback including:

  - summary of overall performance  
  - breakdown of strengths across dimensions  
  - 2–4 key issues  
  - 2–4 targeted improvement recommendations  
  - example answer demonstrating a stronger approach  
  - explicit interviewer evaluation criteria (what is being assessed)

**FR-4.4: Prompt Engineering Techniques**
- The system supports and demonstrates multiple prompt strategies:

  1. Zero-shot (baseline prompt without examples)  
  2. Few-shot (prompt with reference examples; default for production)  
  3. Chain-of-thought (explicit reasoning in evaluation)  
  4. Role-based framing (e.g. strict interviewer perspective)  
  5. Structured output (enforced JSON schema)

- Techniques may rotate across questions or be explicitly selected for testing and comparison

**FR-4.5: Tone Adaptation**
- Feedback tone aligns with the selected interviewer persona:

  - Friendly: supportive and encouraging  
  - Neutral: objective and balanced  
  - Strict: direct and improvement-focused  

- Tone affects delivery, not scoring logic

**FR-4.6: Solution Reasoning Evaluation (Phase 3)**
- Evaluation extends beyond content to assess how the solution was derived

- Assessment includes:

  - logical flow and clarity of reasoning  
  - transparency of decision-making  
  - awareness and articulation of trade-offs  
  - strength of justification for the chosen approach  

- Reasoning quality is captured within the “Problem-Solving Approach” dimension

**FR-4.7: “Why” Explanation Feedback (Phase 3)**
- The system explicitly evaluates the user’s ability to justify decisions

- Feedback addresses:

  - rationale for the chosen approach over alternatives  
  - use of evidence, constraints, and experience  
  - clarity in explaining trade-offs and decisions  

- Feedback is presented within a dedicated “Problem-Solving Assessment” section

- Example guidance:

  - Strong: “Clear justification grounded in real-world constraints.”  
  - Improvement: “Solution is valid, but the reasoning behind the choice is not clearly explained.”  

**FR-4.8: CV vs JD Gap Analysis (Phase 2)**
- Where both CV and job description are provided:

  - the system compares extracted CV attributes against role requirements  
  - identifies missing skills and weak coverage areas  
  - generates targeted follow-up questions addressing identified gaps  

- Gap analysis informs question selection and distribution (FR-2.5)

- Insights are incorporated into:
  - follow-up questions  
  - session summary report  

- Example:
  - identified gap: distributed systems  
  - generated question: “Design a service handling 1M requests per second.”

---

#### 5. Report Generation & Download

**FR-5.1: Question-Level Report (Per Answer, Phase 3)**
- A report is generated for each evaluated response, including:

  - question presented  
  - user’s original answer  
  - evaluation scores across all five dimensions  
  - identified key issues  
  - targeted improvement recommendations  
  - example answer demonstrating a stronger approach  
  - recommended follow-up question  
  - CV profile summary (if provided)  
  - identified skill gaps (if job description is provided)  

- Output formats:
  - PDF
  - JSON

- Filename format:
  - interview_evaluation_Q{n}_{timestamp}.pdf

**FR-5.2: Session Summary Report (End of Session, Phase 1 basic / Phase 3 advanced export)**
 - Upon completion of all 5 base questions, a session summary report is generated, including:

  - overall performance summary  
  - aggregated strengths across all responses  
  - recurring weaknesses and behavioural patterns  
  - recommended focus areas for improvement  
  - list of questions attempted with associated scores  
  - CV context summary (if provided)  
  - gap analysis summary (if job description is provided)  
  - estimated interview readiness rating  

- Output formats:
  - PDF
  - JSON

- Filename format:
  - interview_session_summary_{timestamp}.pdf
    - The session report consolidates insights into a prioritised improvement roadmap based on recurring weaknesses and identified skill gaps

**FR-5.3: Visual Report Components (Phase 3)**
- Reports include visual elements to support interpretation:

  - radar (spider) chart representing all five evaluation dimensions  
  - progress indicators showing improvement across questions (Q1–Q5)  
  - trend analysis where multiple sessions are available  
  - colour-coded performance indicators (e.g. red, amber, green)  

---

#### 6. Session State Management

**FR-6.1: Session Persistence (Phase 1)**
- User progress is maintained within session state (no persistent database required for MVP)

- Session state includes:
  - all generated questions  
  - all submitted answers  
  - evaluation results and feedback  
  - timestamps and interaction history  
  - configuration inputs (role, difficulty, persona, response style)

- The session expires:
  - on browser close, or  
  - after 24 hours of inactivity  

- All session data is cleared upon expiry
  - Session state is isolated per user session and is not shared across users or browser instances

**FR-6.2: Sidebar Persistence (Phase 1)**
- The sidebar remains visible and consistent across all screens

- The sidebar displays current configuration:
  - role  
  - difficulty  
  - interviewer persona  
  - response style  
  - job description (if provided)  
  - CV status (if uploaded)

- Sidebar behaviour:
  - remains stable across interactions  
  - does not reload or shift unexpectedly  
  - reflects current session state at all times  

**FR-6.3: Restart Capability (Phase 1)**
- Users may restart the session at any time

- Restart behaviour:
  - clears all questions, answers, and evaluation data  
  - resets session progression  
  - retains configuration inputs for convenience  

- A confirmation step is required prior to restart to prevent accidental data loss

---

### Non-Functional Requirements

**NFR-1: Performance**
- API response time:
  - < 8 seconds for question generation  
  - < 10 seconds for evaluation and feedback generation  

- UI responsiveness:
  - all user interactions (clicks, typing, navigation) respond within 200ms  

- Initial load time:
  - < 2 seconds under standard network conditions  
    - Progressive loading indicators are used for all API-driven operations exceeding 1 second

**NFR-2: Reliability**
- Uptime target:
  - 99% availability for MVP  

- Error handling:
  - graceful degradation in the event of API or network failure  
  - clear, user-friendly error messaging  

- Session resilience:
  - recovery from transient network interruptions without loss of session state  

- Data integrity:
  - no loss of submitted user input during interruptions or retries  

**NFR-3: Scalability**
- Concurrent usage:
  - support for 1,000+ active sessions  

- Architecture:
  - stateless backend with session-based state management  
  - no persistent database required for MVP  

- Cost model:
  - usage-based scaling via API calls  
  - predictable cost proportional to usage volume  

**NFR-4: Security**
- Input handling:
  - all inputs validated and sanitised prior to processing  

- Prompt injection protection:
  - detection via keyword filtering and LLM-based classification  
  - enforced at submission stage  

- API security:
  - API keys stored securely on the server  
  - no exposure to client-side environments  

- Data privacy:
  - no persistent storage of personal data in Phase 1  
  - session data cleared on expiry or restart  
    - CV and job description inputs are treated as sensitive user data and processed only within the active session context

**NFR-5: Accessibility**
- Compliance:
  - aligned with WCAG 2.1 AA standards  

- Usability:
  - full keyboard navigation support  
  - accessible form inputs and controls  

- Compatibility:
  - responsive layout for desktop and tablet devices  
  - screen reader compatibility with labelled UI elements  

---
