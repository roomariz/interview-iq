# Personalisation and adaptation

## Feature Priority

### 1. CV Input and Extraction

- [x] 🚨 frontend: Add CV upload support for PDF and text input in the setup screen mock-up
- [x] 🚨 frontend: Extend setup screen with CV upload, job description, and start interview action to match setup screen
- [x] 🚨 frontend: Add CV upload input to setup flow without changing the sidebar or main panel structure
- [x] 🚨 backend: Extract CV content into structured profile data
- [x] 🚨 frontend: Store extracted CV profile in session state
- [x] 🧪 backend: Unit test CV extraction schema validation
- [x] 🧪 backend: Unit test PDF CV upload parsing
- [x] 🧪 backend: Unit test text CV upload parsing
- [x] 🧪 frontend: Integration test CV upload to profile flow

### 2. Job Description Input

- [x] 🚨 frontend: Add job description input in the setup screen layout
- [x] 🚨 frontend: Add job description input to setup flow while keeping the mock-up hierarchy
- [x] 🚨 frontend: Wire setup submission to start interview using CV and JD inputs from the setup screen
- [x] 🚨 backend: Parse and validate the job description text
- [x] 🚨 backend: Add graceful fallback when JD is missing (✅ returns "—" when empty)
- [x] 🧪 backend: Unit test job description parsing
- [x] 🧪 backend: Unit test missing JD fallback
- [x] 🧪 frontend: Manual test JD input behaviour (integrated in session state flow)

### 3. Gap Analysis

- [x] 🚨 backend: Implement CV versus JD gap analysis
- [x] 🚨 frontend: Surface missing or weak skill areas in the feedback-style screen design
- [x] 🚨 frontend: Show clear guidance from the gap analysis without introducing new UI patterns
- [x] 🧪 backend: Unit test gap detection logic
- [x] 🧪 backend: Unit test gap summary generation
- [x] 🧪 frontend: Integration test CV to JD comparison flow

### 4. Personalised Question Generation

- [x] 🚨 backend: Personalise questions using CV context
- [x] 🚨 backend: Personalise questions using JD context
- [x] 🚨 backend: Keep the question flow aligned with the user profile
- [x] 🧪 backend: Unit test personalised question construction
- [x] 🧪 backend: Unit test prompt context assembly
- [x] 🧪 frontend: Integration test personalised question flow

### 5. Weighted Distribution and Follow-Ups

- [x] 🚨 backend: Add weighted question distribution across question types
- [x] 🚨 backend: Generate adaptive follow-up questions from detected gaps
- [x] 🚨 backend: Keep follow-up behaviour predictable and testable
- [x] 🧪 backend: Unit test weighted distribution logic
- [x] 🧪 backend: Unit test adaptive follow-up generation
- [x] 🧪 frontend: Integration test follow-up selection flow

### 6. Personalisation Verification

- [x] 🚨 backend: Test CV extraction with valid and invalid input
- [x] 🚨 backend: Test gap analysis with matching and mismatched profiles
- [x] 🚨 frontend: Confirm personalisation is working end to end
- [x] 🧪 frontend: Full personalisation regression test
- [x] 🧪 frontend: Manual test using realistic CV and JD samples

## HTTP backend separation Complete ✅
