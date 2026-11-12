# Phase 3: Advanced Evaluation and Reporting

## Feature Priority

### 1. Reasoning Evaluation

- [x] 🚨 backend: Add reasoning evaluation for decision-making quality
- [x] 🚨 backend: Score trade-off awareness and justification quality
- [x] 🚨 backend: Keep evaluation output structured and deterministic
- [x] 🧪 backend: Unit test reasoning score calculation
- [x] 🧪 backend: Unit test trade-off detection logic
- [x] 🧪 backend: Unit test deterministic evaluation parsing
- [x] 🧪 backend: Integration test evaluation pipeline output

### 2. Feedback Expansion

- [x] 🚨 frontend: Add "why" feedback that explains answer quality in the feedback mock-up
- [x] 🚨 frontend: Highlight how the user can improve their reasoning while matching feedback screen
- [x] 🚨 frontend: Keep feedback consistent across personas and screen states
- [x] 🧪 frontend: Unit test "why" feedback generation
- [x] 🧪 frontend: Unit test recommendation wording
- [x] 🧪 frontend: Manual test feedback readability

### 2.1 Feedback Memory and Trust Refinement

- [x] 🚨 frontend: Add memory filtering and a cap so older follow-up context does not overwhelm the current review
- [x] 🚨 frontend: Add a follow-up escalation ceiling so repeated practice does not keep increasing the follow-up stage indefinitely
- [x] 🚨 frontend: Make UI behaviour trust-driven so score certainty changes the prominence and tone of feedback elements
- [x] 🚨 frontend: Make takeaway generation stricter so it only emits one concrete action with a clear priority
- [x] 🚨 frontend: Expose memory visibility to the user so prior takeaways and follow-up focus are visible in the interface
- [x] 🧪 frontend: Unit test memory filtering and capping behaviour
- [x] 🧪 frontend: Unit test follow-up escalation ceiling handling
- [x] 🧪 frontend: Unit test trust-driven UI state changes
- [x] 🧪 frontend: Unit test stricter takeaway generation
- [x] 🧪 frontend: Manual test memory visibility in the feedback view

### 2.2 Feedback Rules and Acceptance Criteria

- [x] 🚨 frontend: Convert concepts into deterministic rules, constraints, and acceptance criteria for follow-up, memory, trust, and takeaway behaviour
- [x] 🚨 frontend: Define escalation logic so follow-up stages advance predictably and stop at the configured ceiling
- [x] 🚨 frontend: Define a memory eviction policy so older entries are removed in a controlled order when the cap is reached
- [x] 🚨 frontend: Define trust-driven UI rules so visual emphasis changes only when trust thresholds are met
- [x] 🚨 frontend: Define takeaway validation rules so each takeaway remains single-action, prioritised, and reviewable
- [x] 🧪 frontend: Unit test escalation logic definition
- [x] 🧪 frontend: Unit test memory eviction policy
- [x] 🧪 frontend: Unit test trust-driven UI rules
- [x] 🧪 frontend: Unit test takeaway validation rules

### 3. Reporting

- [x] 🚨 backend: Add question-level report generation in PDF format
- [x] 🚨 backend: Add question-level report generation in JSON format
- [x] 🚨 backend: Add session summary report with gap insights
- [x] 🚨 backend: Add session summary recommendations
- [x] 🧪 backend: Unit test PDF report generation
- [x] 🧪 backend: Unit test JSON report generation
- [x] 🧪 backend: Unit test session summary report content
- [x] 🧪 backend: Integration test question-to-report flow

### 4. Analytics

- [x] 🚨 backend: Add richer analytics for score trends across the session
- [x] 🚨 backend: Add improvement tracking across repeated practice attempts
- [x] 🚨 backend: Add export-friendly formatting for reports
- [x] 🧪 backend: Unit test trend calculation
- [x] 🧪 backend: Unit test improvement tracking
- [x] 🧪 backend: Unit test export formatting

### 5. Reporting Verification

- [x] 🚨 frontend: Confirm report exports work correctly against the report mock-ups
- [x] 🚨 frontend: Confirm reasoning scores are readable and stable in the feedback layout
- [x] 🚨 frontend: Run a full session test for reporting output and screen consistency
- [x] 🧪 frontend: Full evaluation and reporting regression test
- [x] 🧪 frontend: Manual test download and open report files

### 6. Calibration Guardrails

- [x] 🚨 backend: The system prevents the six-case calibration dataset from being used as a real scoring calibration basis
- [x] 🚨 backend: The system keeps the `borderline` versus `borderline pass` compatibility rule in one place so the frontend remains stable
- [x] 🚨 backend: The system keeps score normalisation disabled until there are at least 30 to 50 labelled answer examples across weak, borderline, good, and excellent answers
- [x] 🚨 backend: The system runs a calibration-data review check before any future normalisation switch can be enabled

### 7. Enforcement Additions

- [x] 🚨 backend: runtime enforcement for normalisation
- [x] 🚨 backend: calibration output visibility
- [x] 🚨 backend: compatibility assertions
- [x] 🧪 backend: guardrail test case

### 8. Key Shift

- [x] 🚨 backend: Change the rule language from "developers should follow rules" to "system prevents incorrect behaviour"

### 9. Phase 4 Carry-Over

- [x] 🚨 frontend: Explore richer persona presets for interviewer simulation within the existing sidebar structure
- [x] 🚨 frontend: Explore session recovery for refresh and reconnect scenarios while preserving the defined screens
- [x] 🚨 backend: Decide how session history should behave

## Phase 3 Complete ✅
