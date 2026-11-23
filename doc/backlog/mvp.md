# Minimum viable product

## Feature Priority

### 1. Core App Shell and Setup

- [x] 🚨 frontend: Create the Streamlit app shell and navigation flow
- [x] 🚨 frontend: Build the welcome screen to match `doc/product_requirement/mock_ups/1-welcome screen.md`
- [x] 🚨 frontend: Build the setup screen to match `doc/product_requirement/mock_ups/2-Set up screen 2.png`
- [x] 🚨 frontend: Fix duplicate Streamlit button IDs in the app shell
- [x] 🚨 frontend: Add role selection
- [x] 🚨 frontend: Add difficulty selection
- [x] 🚨 frontend: Add interviewer persona selection
- [x] 🚨 frontend: Add response style selection
- [x] 🚨 frontend: Add CV upload paste option with conditional text area
- [x] 🚨 frontend: Add temperature selection

### 2. Session State and Flow Control

- [x] 🚨 frontend: Add session state for questions, answers, feedback, and summary data with welcome/setup/q&a/feedback/summary transitions
- [x] 🚨 frontend: Add restart and exit session behaviour that preserves the mock-up screen structure
- [x] 🚨 frontend: Add loading states for long-running actions without changing the defined layout
- [x] 🧪 frontend: Unit test session state initialisation
- [x] 🧪 frontend: Unit test restart and exit behaviour
- [x] 🧪 frontend: Unit test loading state toggles
- [x] 🧪 frontend: Integration test state persistence during navigation
- [x] 🚨 frontend: Build answer submission handling for the question-and-answer screen mock-up
- [x] 🚨 frontend: Show clear validation messages within the question-and-answer screen layout

### 3. OpenRouter Integration - Complete

- [x] 🚨 backend: Set up OpenRouter API client
- [x] 🚨 backend: Load API key from environment variables
- [x] 🚨 backend: Add API error handling and retry behaviour
- [x] 🧪 backend: Unit test client configuration
- [x] 🧪 backend: Unit test environment variable loading
- [x] 🧪 backend: Unit test API error and timeout handling
- [x] 🧪 backend: Integration test mocked OpenRouter call

### 4. Question Generation

- [x] 🚨 backend: Build the core question generation loop
- [x] 🚨 backend: Generate role-based interview questions
- [x] 🚨 backend: Keep question flow stable across the session
- [x] 🧪 backend: Unit test question generation prompt assembly
- [x] 🧪 backend: Unit test role-based question generation
- [x] 🧪 backend: Unit test question sequence progression
- [x] 🧪 backend: Integration test full question loop

### 5. Answer Handling and Validation

- [x] 🚨 frontend: Build answer submission handling for the question-and-answer screen mock-up
- [x] 🚨 backend: Validate answer length and relevance
- [x] 🚨 backend: Block prompt injection attempts
- [x] 🚨 frontend: Show clear validation messages within the question-and-answer screen layout
- [x] 🧪 backend: Unit test answer length validation
- [x] 🧪 backend: Unit test relevance validation
- [x] 🧪 backend: Unit test prompt-injection blocking
- [x] 🧪 frontend: Manual test validation error messages

### 6. AI Evaluation and Feedback

- [x] 🚨 backend: Implement structured AI evaluation for the core dimensions
- [x] 🚨 frontend: Render feedback scores and improvement notes to match `doc/product_requirement/mock_ups/4-Feedback.md`
- [x] 🚨 frontend: Show strengths and weak points clearly in the feedback panel layout
- [x] 🧪 backend: Unit test evaluation schema parsing
- [x] 🧪 frontend: Unit test feedback formatting
- [x] 🧪 frontend: Unit test score display mapping
- [x] 🧪 frontend: Integration test question answer to feedback flow

### 7. Session Summary

- [x] 🚨 frontend: Add the session summary screen to match `doc/product_requirement/mock_ups/7-Session-Summary.md`
- [x] 🚨 backend: Add basic report download
- [x] 🚨 backend: Summarise performance across the session
- [x] 🚨 frontend: Make the summary readable and testable while preserving the mock-up structure
- [x] 🧪 backend: Unit test summary aggregation
- [x] 🧪 frontend: Unit test summary rendering data shape
- [x] 🧪 frontend: Integration test final summary output
- [x] 🧪 frontend: Manual test summary screen content

### 8. MVP Verification

- [x] 🚨 backend: All 172 unit tests pass
- [x] 🚨 frontend: Run the app end to end after this cycle
- [x] 🚨 frontend: Confirm the full flow is working and testable
- [x] 🚨 backend: Fix anything blocking the next phase
- [x] 🧪 frontend: Full end-to-end regression test
- [x] 🧪 frontend: Verify no blocked path before moving on

## Provider integration Complete ✅
