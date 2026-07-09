Purpose & Scope
- Audience: product manager (non-technical), engineering team, and agent(s).
- Objective: surface only critical technical choices to the PM with clear, non-technical impacts and recommended options to maximize MVP speed.
- When to update: whenever a policy or escalation threshold changes. Include a one-line changelog entry with each update.

Agent vs PM responsibilities
- Agent responsibility: propose implementations, run experiments, prepare ADRs, and implement non-escalated changes.
- Escalation criteria: escalate to PM when a choice will likely (any of):
  - change schedule by >1 week;
  - materially increase recurring cost;
  - add a new external dependency or vendor; or
  - change user-facing behavior or compliance/security posture.

Decision Escalation Template
- Title: short decision name
- Context: 1-2 lines why decision is needed
- Options: enumerated options, with recommended option flagged
- Recommended option: single choice with 1-2 sentence rationale
- Non-technical impact (Time / Cost / Risk):
  - Time: estimated delta to delivery (e.g. +3 days)
  - Cost: low/medium/high and rough $ if available
  - Risk: low/medium/high (maintenance/operational/user impact)
- Engineering summary: 2-4 lines tradeoffs (pros/cons)
- Confidence & assumptions: brief note on estimate confidence and assumptions
- Decision record: final choice, approver, date

Worked Example
- Title: Schema validation library
- Context: Need runtime-validated schemas for prediction input/output
- Options:
  1) Pydantic v2 (recommended)
  2) Marshmallow
  3) Hand-rolled validation
- Recommended option: Pydantic v2
- Non-technical impact:
  - Time: +1 day to integrate
  - Cost: low
  - Risk: low
- Engineering summary: Pydantic v2 provides typed models, validation, and faster iteration. Marshmallow is more verbose; hand-rolled increases maintenance risk.
- Confidence & assumptions: medium confidence; assumes one engineer with Python experience.

Agent Automated Estimates
- The agent will provide best-effort Time/Cost/Risk estimates when surfacing choices. Each estimate will include a confidence label (high/medium/low) and the core assumptions used.

Execution Policies (MVP-focused)
- Evidence Requests: Components must create Evidence Requests when additional information is required; requests must include an acceptance criterion.
- Evidence iteration limit: Maximum Evidence Resolution Iterations = 4
- Recursion/hop limit: Hard limit of 3 iterative search hops per execution block
- Escalation on cost/time: Agent must escalate if estimated engineering time > 1 week or estimated monthly cost > $100
- Schema safety: All outputs must be schema-validated before persisting or exposing externally

MVP Priorities & Acceptance Criteria
- B1.1 Base Environment Setup & API Core Interfacing — Priority: HIGH
  - Acceptance: repo boots in Codespaces/dev image; basic API reachable locally
- B1.2 Declarative Schema Definitions via Pydantic — Priority: HIGH
  - Acceptance: models implemented; validation blocks invalid writes
- B1.3 Context-Driven Orchestration Loop & Threshold Checkers — Priority: HIGH
  - Acceptance: orchestrator runs predictions with evidence request routing; state persisted to state.json
- B1.4 File-based Persistence for MVP — Priority: MEDIUM
  - Acceptance: human-inspectable JSON files for key state

ADR & Decision Logging
- ADR format: Title, Date, Decision, Alternatives, Rationale (short), Consequences, Approver
- Place ADRs in docs/adr/ (create if missing) and reference relevant sections in `Stock_Analyzer_Engineering_Specification.md`

How to Update This File
- Keep this file small. Each update must include a one-line changelog. For policy changes, include a short rationale and notify the PM.

References
- Engineering Spec: [Prediction Orchestrator and Evidence policy](Stock_Analyzer_Engineering_Specification.md#L134-L140)
- Evidence Resolution Policy: [Evidence iteration limit and policy](Stock_Analyzer_Engineering_Specification.md#L221-L226)
- ADR log: [Architecture Decision Log](Stock_Analyzer_Engineering_Specification.md#L387-L395)
- Product Specs: PRODUCT_SPECS.md
- Backlog: Stock_Analyzer_Backlog.txt
