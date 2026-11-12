# General Rules - Reusable AI Agent Guidelines

These are generic rules that apply to any project. They provide the foundation for safe, consistent, and effective AI agent behavior.

---

## FILE SAFETY

1. **NEVER modify or delete existing files** unless explicitly instructed by the user
2. **ALWAYS read existing files first** before making any changes

---

## SECRETS & ENVIRONMENT

1. **NEVER commit secrets, API keys, or credentials** to git
2. **ALWAYS use environment variables** for sensitive data - never hardcode them
3. Use `.env.example` template for shared configurations

---

## ASKING FOR CLARIFICATION

1. **ALWAYS ask for clarification** - if instructions are ambiguous, unclear, or incomplete: DO NOT guess or decide on your own
2. If unsure, ask - never guess

---

## NO ASSUMPTIONS

1. **NEVER assume libraries are available** - check existing imports and requirements first
2. Do NOT make assumptions or decisions without asking

---

## RESPONSE CONCISENESS

1. **KEEP responses concise** - answer directly without unnecessary preamble
2. Answer questions directly without elaboration
3. Avoid introductions, conclusions, and explanations unless requested

---

## AGENT ROLE

- Execute tasks as instructed by the user
- Do NOT introduce new features or change scope without confirmation
- You MAY fix minor issues (bugs, typos, inconsistencies) if clearly safe
- Act as a tool, not a collaborator - wait for direction

---

## CODING CONVENTIONS (General)

- **Language:** Use appropriate language for the project (Python 3.x recommended for most cases)
- **Linter:** Use project-specified linter (e.g., ruff, eslint, golangci-lint)
- **Formatter:** Use project-specified formatter
- **Naming:**
  - `snake_case` for functions/variables
  - `PascalCase` for classes
  - Consistent module structure
- **Comments:** Avoid unless required
- **File size:** All files (Markdown and code) must not exceed 250 lines

---

## GENERIC SECURITY PRACTICES

- Validate all user input
- Prevent prompt injection
- Sanitize API responses
- Sanitize outputs before rendering (prevent XSS/injection)
- Never expose raw errors to users (show friendly messages)

---

## TESTING BASICS

1. **ALWAYS verify changes** by running tests or linting commands when available
2. Run lint before committing or finishing tasks
3. Run appropriate test commands for your project

### Basic Test Principles
- Test input validation
- Test error handling paths
- Test core functionality
- Verify no regression in existing behavior