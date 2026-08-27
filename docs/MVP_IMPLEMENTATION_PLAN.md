# Personalized Chuyên Toán Coach — Detailed MVP Implementation Plan

**Document version:** 2.0  
**Status:** implementation handover  
**Primary client:** mobile/tablet responsive PWA  
**Core revision in this version:** one student profile may contain multiple active target examinations.

---

## 1. Product definition

The MVP is a goal-oriented coaching system for Vietnamese competitive mathematics. It is not a general chat application and it is not a generic homework solver.

A student should be able to:

1. Create one study profile.
2. Add multiple target examinations or schools to that profile.
3. Set an exam date, target score, and priority for each target.
4. Receive one combined daily training plan that balances:
   - skills shared by several target examinations;
   - urgent weaknesses for the nearest examination;
   - target-specific preparation;
   - overdue review.
5. Read correctly rendered mathematical problems.
6. Use curated interactive geometry where relevant.
7. Solve on ordinary paper and take a photo.
8. Review and correct the AI transcription with visual mathematical editing.
9. Receive structured step-level grading and feedback.
10. Request progressively stronger hints without immediately revealing the complete solution.
11. Open short concept explanations and visualizations in the context of the current problem.
12. Retry the problem.
13. Have the system record skill evidence, mistakes, hint use, solve time, and review needs.
14. See progress for each target examination and for the shared mathematical skill graph.
15. Review old mistakes, complete scheduled reviews, earn XP, and maintain a streak.

The core loop is:

```text
Multiple exam targets
        ↓
Combined daily plan
        ↓
Problem
        ↓
Paper solution + photo
        ↓
Confirmed transcription
        ↓
Step evaluation
        ↓
Hint / concept / retry
        ↓
Learner-state update
        ↓
Review scheduling
        ↓
Next combined plan
```

---

## 2. MVP boundaries

### 2.1 Included

| Area | MVP capability |
|---|---|
| Platform | Responsive PWA for phones and tablets |
| Targeting | Multiple active examinations in one student profile |
| Content | Curated exercise, skill, concept, rubric, solution, hint, and geometry data |
| Math display | Typed math content rendered by the application |
| Math correction | Visual formula editing; no raw-LaTeX requirement for students |
| Geometry | Curated interactive scenes and a restricted action vocabulary |
| Input | Camera capture and existing-photo upload |
| AI transcription | Multimodal image-to-structured-solution transcription |
| Confirmation | Student corrects the transcript before grading |
| AI grading | Step status, root error, dependent error, score, and concise feedback |
| Hints | Progressive hint ladder with optional geometry actions |
| Learner state | Structured skill, mistake, independence, hint, time, and review evidence |
| Planning | Deterministic multi-target daily-plan algorithm |
| Engagement | XP, streak, session completion, mistake notebook, individual challenges |
| Internal quality tools | Content preview and flagged-attempt inspection |
| Content workflow | Version-controlled YAML/JSON and seed scripts |

### 2.2 Excluded

- Native iOS or Android application.
- Capacitor or another native wrapper.
- Direct Apple Pencil or S Pen writing.
- Arbitrary student-created geometry constructions.
- Runtime AI generation of executable geometry code.
- Voice conversation.
- General-purpose chat as the main interface.
- Public leaderboards or social feeds.
- Teacher marketplace.
- Full teacher/admin product.
- General-purpose CMS.
- All Vietnamese examinations at launch.
- All K–12 mathematics.
- Full offline operation.
- General RAG framework.
- Dedicated vector database.
- Custom foundation-model training.
- Fine-tuning before a validated pilot dataset exists.
- Predicted entrance probability or predicted exam score before calibration data exists.

---

## 3. Decision timing

No implementation agent may invent product values. However, decisions must block only the stage that actually needs them. Internal development may proceed with synthetic fixtures, mock exam records, deterministic fake AI, and non-personal test images.

| Decision area | Must be resolved before | Does not block |
|---|---|---|
| Supported examination set | Importing or publishing real exam content in Milestone 2 | Milestone 1 foundation and mocked interaction work |
| Pilot cohort and operations | Inviting external participants in Milestone 12 | Internal implementation and testing in Milestones 1–11 |
| AI provider benchmark and production-provider confirmation | Sending real participant data or starting an external pilot | Provider-adapter implementation and internal provider trials using synthetic/non-personal inputs |
| Legal, privacy, and consent review | Collecting real minors' data or starting an external pilot | Internal work using synthetic/non-personal fixtures |
| Content provenance approval | Importing or publishing real third-party content | Schema and UI development using original synthetic fixtures |
| Numeric release and pilot gates | Starting the external pilot | Internal product iteration and engineering checks |

The project owner is the sole MVP product decision authority. Specialist legal, privacy, rights, security, or mathematics review is supporting evidence when the decision requires that expertise; it is not a separate product-governance layer.

### 3.1 Supported examination set

The system architecture supports any number of targets per profile, but the MVP content release must name a finite supported set.

Example only:

```text
SUPPORTED_EXAMS = [PTNK, HCMC_Specialized]
```

The project owner must decide the real list before real exam content is imported or published. A student may select any subset of the supported set. Until then, internal development must use clearly synthetic exam records and preserve the multi-exam model.

### 3.2 Pilot cohort

Before an external pilot, the project owner must record:

```text
student grade/age range
number of invited students
location
supported language
parent/guardian consent requirement
supported devices
pilot start/end criteria
```

This cohort decision does not block internal implementation.

### 3.3 AI provider benchmark

Do not assume that a consumer ChatGPT interaction and an API model behave identically.

Before integrating a production provider, benchmark representative samples that include:

```text
clean handwriting
messy but readable handwriting
mixed Vietnamese and mathematics
cross-outs and insertions
correct standard solutions
correct alternative solutions
subtle mathematical errors
incomplete solutions
geometry solutions
```

Selection criteria:

```text
transcription correction burden
step segmentation quality
grading quality
false criticism of valid steps
alternative-solution acceptance
hint quality
latency
cost
data-handling terms
```

The specification may evolve while the interaction experience is built. A development provider may be selected by the project owner and integrated behind the provider adapter in Milestone 6 using synthetic/non-personal inputs. Benchmark evidence, production-provider confirmation, and applicable data-handling approval gate real participant data and the external pilot, not application development.

### 3.4 Legal and privacy review

Before inviting minors, obtain appropriate review for:

```text
child data
parent/guardian consent
automated educational assessment
AI-provider data processing
image retention
research/model-improvement consent
account deletion and data export
```

This plan does not provide legal conclusions. This review gates real participant data and the external pilot; it does not gate internal development with synthetic/non-personal fixtures.

### 3.5 Internal device-development matrix

Internal phone and tablet development uses browser emulation first:

```text
compact phone: Chromium, 360 × 640 viewport
Android phone: Playwright Pixel 7 descriptor
iPhone: Playwright iPhone 13 WebKit descriptor
tablet portrait: Playwright iPad Pro 11 WebKit descriptor
tablet landscape: Playwright iPad Pro 11 landscape WebKit descriptor
```

Use Android Emulator later for Android browser, camera, permission, and upload behavior that browser emulation cannot represent faithfully. Apple iOS/iPadOS Simulator requires a macOS/Xcode environment and is therefore a pre-pilot validation path, not a blocker for Linux-based internal development. Physical-device testing is required before an external pilot, not before the first internal MVP.

---

## 4. Architectural principles

1. The frontend never renders arbitrary AI Markdown as canonical content.
2. Mathematical and geometry content uses strict versioned schemas.
3. AI output is untrusted until schema validation succeeds.
4. The student-confirmed transcript is the authoritative grading input.
5. The application, not the LLM, owns learner state and daily planning.
6. SQL retrieval is used when the problem, skill, concept, and student IDs are already known.
7. One profile may have zero, one, or many active exam targets; no domain type may assume exactly one target.
8. Shared skills are modeled once and linked to several examinations.
9. Every attempt references immutable versions of content, prompts, schemas, and model snapshots.
10. Every aggregate learner state can be recomputed from immutable evidence events.
11. AI may trigger only predefined UI and geometry actions.
12. Runtime AI code execution is prohibited.
13. The MVP prioritizes a complete vertical learning loop over broad content coverage.

---

## 5. Technical architecture

```text
┌──────────────────────────────────────────────────────┐
│ Student PWA                                          │
│ Next.js + React + TypeScript                         │
│                                                      │
│ • Multi-exam onboarding                              │
│ • Combined daily plan                                │
│ • Problem view                                       │
│ • KaTeX math rendering                               │
│ • MathLive correction                                │
│ • JSXGraph geometry                                  │
│ • Photo capture                                      │
│ • Feedback, hints, concepts, retry                    │
│ • Per-target and shared progress                     │
└───────────────────────┬──────────────────────────────┘
                        │ HTTPS / SSE
                        ▼
┌──────────────────────────────────────────────────────┐
│ FastAPI application                                  │
│                                                      │
│ • Authentication                                     │
│ • Study profile and exam targets                     │
│ • Content package service                            │
│ • Attempt lifecycle                                  │
│ • AI provider gateway                                │
│ • Learner-state engine                               │
│ • Multi-target coaching policy                       │
│ • Review scheduler                                   │
│ • Reward service                                     │
└───────────────┬────────────────┬─────────────────────┘
                │                │
                ▼                ▼
      PostgreSQL / JSONB    S3-compatible storage
                │
                ▼
      Multimodal AI provider
```

### 5.1 MVP stack

| Layer | Choice |
|---|---|
| Student application | Next.js, React, TypeScript |
| PWA | Web manifest and service worker |
| Read-only mathematics | KaTeX |
| Editable mathematics | MathLive |
| Geometry | JSXGraph |
| API | FastAPI and Pydantic |
| Database | Managed PostgreSQL |
| Flexible rich content | JSONB |
| Images | S3-compatible object storage |
| AI | One benchmark-selected multimodal provider behind an adapter |
| Streaming status | Server-Sent Events |
| Content source | Git-versioned YAML/JSON |
| Retrieval | Relational SQL; no general RAG |
| Authentication | Invite-only pilot accounts |

---

## 6. Repository structure

```text
math-coach/
├── AGENTS.md
├── PLANS.md
├── apps/
│   └── student-web/
│       ├── app/
│       ├── features/
│       │   ├── onboarding/
│       │   ├── exam-targets/
│       │   ├── training/
│       │   ├── problem/
│       │   ├── submission/
│       │   ├── transcription/
│       │   ├── evaluation/
│       │   ├── hints/
│       │   ├── concepts/
│       │   ├── geometry/
│       │   ├── mistakes/
│       │   ├── progress/
│       │   └── rewards/
│       ├── components/
│       │   ├── math/
│       │   ├── geometry/
│       │   └── common/
│       └── lib/
├── services/
│   └── api/
│       ├── app/
│       │   ├── api/
│       │   ├── domain/
│       │   │   ├── content/
│       │   │   ├── profiles/
│       │   │   ├── exam_targets/
│       │   │   ├── attempts/
│       │   │   ├── learner/
│       │   │   ├── coaching/
│       │   │   ├── review/
│       │   │   └── rewards/
│       │   ├── ai/
│       │   ├── database/
│       │   └── security/
│       ├── migrations/
│       └── tests/
├── packages/
│   ├── content-schema/
│   ├── ai-contracts/
│   ├── math-content/
│   ├── geometry-schema/
│   └── api-client/
├── content/
│   ├── exams/
│   ├── problems/
│   ├── concepts/
│   └── geometry/
├── evals/
│   ├── transcription/
│   ├── grading/
│   ├── hints/
│   └── geometry/
├── scripts/
│   ├── validate_content/
│   ├── seed_content/
│   ├── build_eval_set/
│   └── delete_expired_assets/
├── docs/
│   ├── MVP_IMPLEMENTATION_PLAN.md
│   ├── architecture/
│   ├── changes/
│   ├── privacy/
│   └── evaluation/
└── infra/
```

---

## 7. Core content contracts

### 7.1 Typed mathematical content

```typescript
type ContentBlock =
  | { id: string; type: "text"; text: string }
  | { id: string; type: "inline_math"; latex: string }
  | { id: string; type: "display_math"; latex: string }
  | {
      id: string;
      type: "rich_line";
      spans: Array<
        | { type: "text"; text: string }
        | { type: "math"; latex: string }
      >;
    }
  | { id: string; type: "geometry"; sceneId: string }
  | { id: string; type: "image"; assetId: string; alt: string }
  | {
      id: string;
      type: "callout";
      kind: "note" | "warning" | "hint" | "success";
      content: ContentBlock[];
    };
```

### 7.2 Geometry scene

```typescript
interface GeometryScene {
  schemaVersion: string;
  id: string;
  viewport: {
    xMin: number;
    xMax: number;
    yMin: number;
    yMax: number;
  };
  objects: GeometryObject[];
  initialVisibleObjectIds: string[];
  fallbackImageAssetId?: string;
  accessibilityDescription: string;
}
```

MVP object types:

```text
point
segment
line
ray
circle
arc
polygon
angle
midpoint
intersection
perpendicular
parallel
circumcircle
label
```

### 7.3 Geometry actions

```typescript
type GeometryAction =
  | { type: "show"; objectIds: string[] }
  | { type: "hide"; objectIds: string[] }
  | { type: "highlight"; objectIds: string[] }
  | { type: "clear_highlight"; objectIds?: string[] }
  | { type: "focus"; objectIds: string[] }
  | { type: "animate"; objectId: string; animationId: string }
  | {
      type: "ask_select";
      prompt: ContentBlock[];
      allowedObjectIds: string[];
      correctObjectIds?: string[];
    };
```

### 7.4 Transcription result

```typescript
interface TranscriptionResult {
  schemaVersion: string;
  attemptId: string;
  blocks: Array<{
    id: string;
    type: "text" | "math";
    text?: string;
    latex?: string;
    sourceRegion?: {
      x: number;
      y: number;
      width: number;
      height: number;
    };
  }>;
  warnings: Array<{ blockId?: string; message: string }>;
}
```

Block array order is the canonical transcription order. Correction-stage transcription does not
contain reasoning-step IDs or grouping. Reasoning analysis may run only after the learner confirms
this flat document. Text and math variants may alternate within the same visual line; the learner
edits them through one continuous document rather than exposed block rows.

### 7.5 Evaluation result

```typescript
interface EvaluationResult {
  schemaVersion: string;
  attemptId: string;
  score: number;
  maxScore: number;
  steps: Array<{
    stepId: string;
    status:
      | "valid"
      | "valid_implicit"
      | "minor_gap"
      | "major_gap"
      | "root_error"
      | "dependent_error"
      | "uncertain";
    awardedScore: number;
    maximumScore: number;
    feedback: ContentBlock[];
    skillIds: string[];
    mistakeCode?: string;
  }>;
  mainIssueStepId?: string;
  nextAction:
    | "retry"
    | "request_hint"
    | "review_concept"
    | "show_solution"
    | "complete"
    | "manual_review";
  skillEvidence: Array<{
    skillId: string;
    achievement: number;
    independent: boolean;
    highestHintLevelUsed: number;
  }>;
}
```

---

## 8. Database design

### 8.1 General rules

1. PostgreSQL is authoritative.
2. Relational tables store identity, relationships, events, and current state.
3. JSONB stores versioned rich content and validated AI payloads.
4. Image bytes remain in object storage.
5. Attempts reference immutable content versions.
6. AI runs record provider, model snapshot, prompt version, schema version, latency, and cost.
7. Learner aggregates are rebuildable from evidence events.
8. The schema must represent multiple exam targets without duplicated user profiles.

### 8.2 User and study profile

#### `users`

```text
id
account_status
display_name
pilot_code
created_at
deleted_at
```

#### `study_profiles`

One active study profile represents one preparation cycle.

```text
id
user_id
name
weekly_study_minutes
status
created_at
updated_at
```

#### `student_exam_targets`

```text
id
study_profile_id
exam_id
exam_date
target_score
priority_rank
status
created_at
updated_at
```

Rules:

- `priority_rank` is unique within an active study profile.
- A profile may contain many active targets.
- No target is implicitly primary; rank and date drive planning.
- A target score is a student goal, not a system prediction.

### 8.3 Exams and exam-skill configuration

#### `exams`

```text
id
code
name
region
status
```

#### `exam_cycles`

```text
id
exam_id
year
exam_date
maximum_score
content_version
status
```

#### `exam_skill_weights`

Expert-configured and versioned; not claimed as statistical truth.

```text
id
exam_cycle_id
skill_id
weight
source_note
version
```

### 8.4 Skills and concepts

#### `skills`

```text
id
code
name
description
domain
status
```

#### `skill_edges`

```text
parent_skill_id
child_skill_id
relation_type
```

Relations:

```text
prerequisite
related
subskill
```

#### `concepts` and `concept_versions`

```text
concepts:
  id
  code
  name
  current_version_id
  status

concept_versions:
  id
  concept_id
  version
  content_jsonb
  geometry_scene_version_id
  created_at
  published_at
```

### 8.5 Problems and exam relevance

#### `problems`

```text
id
external_code
origin_exam_cycle_id
year
problem_number
current_version_id
status
```

#### `problem_versions`

```text
id
problem_id
version
statement_jsonb
maximum_score
difficulty_band
estimated_minutes
geometry_scene_version_id
content_hash
created_at
published_at
```

#### `problem_exam_relevance`

A problem may be useful for several target examinations.

```text
problem_version_id
exam_cycle_id
relevance_level
relevance_note
```

`relevance_level` uses a documented finite scale defined in configuration. The team must not mix different scales.

#### `problem_skill_links`

```text
problem_version_id
skill_id
role
importance
```

Roles:

```text
primary
secondary
prerequisite
diagnostic
```

#### `reference_solutions`

```text
id
problem_version_id
solution_code
content_jsonb
method_label
expert_verified
```

#### `rubric_items`

```text
id
problem_version_id
rubric_code
description_jsonb
maximum_score
skill_id
order_index
```

#### `problem_hints`

```text
id
problem_version_id
hint_level
content_jsonb
geometry_actions_jsonb
reveals_complete_solution
concept_id
```

### 8.6 Sessions and multi-target attribution

#### `learning_sessions`

```text
id
study_profile_id
planned_date
planned_minutes
status
started_at
completed_at
summary_jsonb
```

#### `session_items`

```text
id
session_id
problem_version_id
position
selection_reason
planned_minutes
status
```

#### `session_item_target_links`

Records which targets the planner intended each item to support.

```text
session_item_id
student_exam_target_id
contribution_level
```

### 8.7 Attempts, learner evidence, reviews, rewards, and AI runs

Retain the following event-oriented tables:

```text
attempts
attempt_assets
transcript_versions
attempt_steps
evaluations
hint_events
retry_submissions
skill_evidence_events
student_skill_states
mistake_events
review_queue
reward_events
prompt_versions
ai_model_runs
```

Every attempt references the exact problem version and active study profile.

---

## 9. Multi-target coaching policy

The planner is deterministic and auditable. The LLM does not choose the daily plan.

### 9.1 Inputs

```text
active exam targets
exam dates
priority ranks
exam-skill weights
student skill states
review queue
problem-exam relevance
problem-skill links
problem prerequisites
problem history
estimated time
available session minutes
```

### 9.2 Derived target priority

The system calculates a target priority from:

```text
user-defined priority rank
remaining time until exam
weekly target-specific coverage history
```

The exact mapping is configuration, not hard-coded in domain logic. Configuration values must be documented and versioned.

### 9.3 Candidate eligibility

A problem is eligible only when:

```text
it is published
it supports at least one active target
required prerequisites meet the configured minimum state
it has not been completed as a new problem before
its estimated time fits the remaining session budget
it is not blocked by content or quality flags
```

Review problems are allowed to repeat when the review queue explicitly requests them or a transfer variant.

### 9.4 Problem utility

The planner calculates an auditable utility record with separate components:

```text
review urgency
shared-target value
target-specific value
skill need
prerequisite suitability
difficulty suitability
recent repetition penalty
session-time fit
weekly target-balance adjustment
```

Do not collapse these values into an opaque ML score in the MVP.

### 9.5 Selection sequence

1. Select the highest-priority overdue review.
2. Select a high-value shared problem that supports more than one active target when available.
3. Select a target-specific weakness problem for the most urgent under-covered target.
4. Select a mixed exam-style problem.
5. Add an optional challenge only when time remains.

The number of items is determined by the time budget, not a fixed count.

### 9.6 Weekly balance

The planner tracks target-specific coverage over a rolling configured period.

- A shared problem may contribute to several targets.
- A target must not be starved because another exam is nearer unless the configured policy explicitly allows it.
- The plan must explain why every selected problem was chosen.

Example explanation codes:

```text
overdue_review
shared_high_value
urgent_target_weakness
target_coverage_gap
mixed_exam_practice
challenge
```

### 9.7 Progress display

Until calibration data exists, do not display predicted exam scores or admission probability.

Display instead:

```text
skill coverage
review completion
independent mastery
recent practice coverage by target
days remaining
target-specific topic coverage
```

---

## 10. AI workflow

### 10.1 Provider abstraction

```python
class AIProvider:
    async def transcribe_solution(...): ...
    async def evaluate_solution(...): ...
    async def generate_hint(...): ...
```

Implement one real provider and one deterministic fake provider for tests.

### 10.2 Transcription

Input:

```text
problem statement
student image
strict transcription schema
instruction to preserve exactly what the student wrote
```

Output:

```text
one continuous ordered document of typed text and math blocks
warnings
source regions when available
```

The model must not silently correct mathematical mistakes.

### 10.3 Confirmation

The student may:

```text
place a native caret and edit text in place
insert math at the caret
activate and edit existing math visually
reorder formulas through contextual controls
delete a whole formula only after explicit confirmation
confirm
```

Only the confirmed flat version is authoritative downstream input. Reasoning-step detection and
grouping occur, if needed, after confirmation; they are not part of transcription correction.

### 10.4 Evaluation

Input:

```text
problem
confirmed transcript
reference solutions
rubric
known methods
skills
hint history
```

The prompt must state that reference solutions are non-exhaustive and valid alternative methods must be accepted.

Output:

```text
step statuses
root and dependent errors
score
skill evidence
concise feedback
next action
```

### 10.5 Hints

| Level | Behavior |
|---|---|
| 1 | Direct attention without naming the method |
| 2 | Name the relevant concept or object |
| 3 | Suggest a concrete transformation or construction |
| 4 | Show a partial worked step |
| Final | Full solution after explicit action |

### 10.6 Validation and failure handling

1. Validate every AI output against its schema.
2. Reject unknown enums and geometry IDs.
3. Retry once for schema failure.
4. Do not render unvalidated output.
5. Do not fabricate a score after failure.
6. Log model, prompt, schema, latency, tokens, and cost.
7. Route uncertain evaluations to the internal flagged-attempt view.

---

## 11. Math rendering and correction

### 11.1 Read-only mathematics

Use KaTeX behind a controlled renderer.

- Do not display raw LaTeX after a rendering error.
- Show a correctable placeholder.
- Disable trusted commands for untrusted content.
- Bound macro expansion and element size.

### 11.2 Editing

Use MathLive for visual formula editing.

Students must not be required to understand LaTeX.

### 11.3 Confirmation layout

Tablet:

```text
photo | structured transcript
```

Phone:

```text
PHOTO tab | TRANSCRIPT tab
```

### 11.4 Regression corpus

Test at least:

```text
fractions
nested fractions
powers
subscripts
roots
systems
cases
inequalities
congruences
sets
logic
matrices
geometry symbols
Vietnamese mixed with inline math
multi-line derivations
```

Release criterion: no raw TeX leaks in the committed regression suite.

---

## 12. Interactive geometry

### 12.1 Curated scenes

Every released geometry problem has a validated and versioned scene.

AI does not create executable scenes at runtime.

### 12.2 Construction semantics

Store mathematical constructions, not only coordinates.

```json
{
  "id": "M",
  "type": "midpoint",
  "parents": ["B", "C"]
}
```

### 12.3 Allowed student interaction

```text
drag permitted free points
tap/select known objects
show/hide
highlight
move configured sliders
answer visual-selection questions
```

### 12.4 Validation

Reject:

```text
duplicate IDs
unknown parents
construction cycles
unknown action targets
unsupported object types
missing accessibility descriptions
```

Every scene must have a fallback image and description.

---

## 13. Student screens

1. **Pilot login**
2. **Study profile and multiple exam targets**
3. **Combined home/today plan**
4. **Problem and geometry**
5. **Camera/photo preview**
6. **Transcript confirmation**
7. **Evaluation, hint, concept, retry**
8. **Session summary**
9. **Target-specific progress**
10. **Shared skill map**
11. **Mistake notebook and review queue**

The UI must clearly show which target examinations a planned problem supports.

---

## 14. API surface

```text
POST   /auth/pilot-login

GET    /study-profile
POST   /study-profile
PATCH  /study-profile

GET    /exam-targets
POST   /exam-targets
PATCH  /exam-targets/{target_id}
DELETE /exam-targets/{target_id}

GET    /plans/today
POST   /sessions
GET    /sessions/{session_id}
POST   /sessions/{session_id}/complete

GET    /problems/{problem_id}

POST   /attempts
GET    /attempts/{attempt_id}
POST   /attempts/{attempt_id}/assets/presign
POST   /attempts/{attempt_id}/transcribe
POST   /attempts/{attempt_id}/transcripts
POST   /attempts/{attempt_id}/confirm-transcript
POST   /attempts/{attempt_id}/evaluate
POST   /attempts/{attempt_id}/retry
POST   /attempts/{attempt_id}/hints

GET    /concepts/{concept_id}
GET    /progress/shared
GET    /progress/targets
GET    /mistakes
GET    /reviews

GET    /internal/content-preview/{problem_id}
GET    /internal/flagged-attempts
```

---

## 15. Milestones

Implementation priority across Milestones 1–5 is the core human–AI interaction:

```text
paper solution photo
        ↓
visible processing and recovery states
        ↓
structured transcript the student can correct visually
        ↓
explicit student confirmation
        ↓
step feedback, uncertainty, and next action
        ↓
progressive hint or retry
```

Build and review this flow incrementally with deterministic mocks. Do not postpone all UI/UX learning until provider integration.

### Milestone 0 — Internal MVP direction and deferred-gate register

Deliver:

```text
core human–AI interaction priority
single project-owner decision model
decision timing and deferred-gate register
emulator-first phone/tablet development matrix
pre-pilot privacy and consent checklist
pre-publication content provenance checklist
provider benchmark specification
release-quality gate framework
```

Exit when the internal product direction, development-device matrix, and timing of every deferred decision are explicit. Unresolved external-pilot, provider-selection, content-publication, or release items do not block Milestone 1.

### Milestone 1 — Repository and engineering foundation

Deliver:

```text
Next.js application
FastAPI application
PostgreSQL migrations
object storage
invite-only auth
CI
logging
root development commands
responsive interaction shell
```

Exit when an internal test user can log in, open the responsive interaction shell, and upload a synthetic or non-personal test image in the development device matrix.

### Milestone 2 — Versioned content and multi-exam schema

Implement:

```text
exam cycles
multiple exam targets
exam-skill weights
problem-exam relevance
skills
concepts
problem versions
solutions
rubrics
hints
geometry scenes
seed pipeline
content preview
```

Exit when invalid content cannot be imported and attempts reference immutable content.

### Milestone 3 — Mathematical rendering and correction spike

Deliver:

```text
KaTeX renderer
MathLive editor
flat mixed text/math blocks
inline native-caret document correction
formula insert/confirmed-delete/contextual-reorder operations
regression suite
device report
```

Exit when no raw LaTeX appears in the regression suite and confirmation preserves the exact flat
ordered document without reasoning-step grouping. Text and mathematics must flow inline, MathLive
must activate at an existing or newly inserted formula, and no whole formula may be deleted without
learner confirmation.

### Milestone 4 — Interactive geometry engine

Deliver:

```text
scene renderer
approved primitives
construction ordering
touch interactions
validated actions
fallback image
representative fixtures
```

Exit when scenes render deterministically and preserve constraints.

### Milestone 5 — Static end-to-end student slice

Use mocked AI to complete:

```text
multiple-target onboarding
combined daily plan
problem
geometry
photo
mock transcript
correction
mock evaluation
hint
retry
concept
summary
```

Exit when the entire journey works in the emulator-first phone/tablet development matrix. Physical-device and true iOS/iPadOS Simulator validation remain pre-pilot work.

### Milestone 6 — Multimodal transcription

Deliver:

```text
real provider adapter
strict schema
transcription UI
student confirmation
benchmark report
model/prompt versioning
```

Exit when all released transcripts are correctable and no unvalidated output reaches the UI.

### Milestone 7 — Evaluation, scoring, and progressive hints

Deliver:

```text
step evaluation
root/dependent error handling
rubric score
alternative-solution tests
hint ladder
geometry-assisted hints
uncertainty route
gold evaluation report
```

The project owner must confirm numeric gates before an external pilot. Internal thresholds may evolve from measured benchmark and usability evidence; do not present provisional values as validated release claims.

### Milestone 8 — Learner-state engine

Deliver:

```text
skill evidence
mastery transitions
mistake events
review scheduler
hint independence
recomputation tests
```

Exit when state rebuild from events is deterministic.

### Milestone 9 — Multi-target daily coaching

Deliver:

```text
target priority derivation
shared-problem utility
target-specific coverage
review priority
session-time fitting
weekly balance
selection explanations
planner regression tests
```

Exit when the same inputs produce the same plan and every item has an auditable reason.

### Milestone 10 — Concepts, mistakes, progress, and engagement

Deliver:

```text
concept overlay
visualizations
mistake notebook
review flow
session summary
XP
streak
shared progress
target-specific progress
```

Do not add a public ranking.

### Milestone 11 — PWA, device, security, privacy, and release hardening

Deliver:

```text
manifest/service worker
camera fallback
upload retry
signed URLs
file validation
EXIF removal
rate limits
data deletion jobs
account deletion/export
device test report
security checklist
privacy checklist
incident procedure
external-pilot decisions and evidence
```

All privacy, consent, content-rights, device, security, retention, deletion/export, and pilot-operation items that were deferred during internal development must be resolved before this milestone exits.

### Milestone 12 — Closed pilot and go/no-go

Measure:

```text
camera/upload reliability
transcription correction burden
math and geometry rendering failures
AI latency and cost
root-error agreement
false criticism of valid steps
alternative-solution acceptance
hint usefulness
session completion
retry and review behavior
independent solving
unseen-test improvement
student preference versus free-form general AI
```

Proceed only when the structured coaching system demonstrates clear value beyond a general chat workflow.

---

## 16. Critical path

```text
M0 Internal MVP direction
        ↓
M1 Foundation
        ↓
M2 Content + multi-exam schema
        ├───────────────┐
        ↓               ↓
M3 Math UI         M4 Geometry
        └───────────────┘
                ↓
M5 Static vertical slice
                ↓
M6 Transcription
                ↓
M7 Evaluation + hints
                ↓
M8 Learner state
                ↓
M9 Multi-target coaching
                ↓
M10 Concepts + engagement
                ↓
M11 Hardening + pre-pilot gates
                ↓
M12 Pilot
```

Content preparation continues in parallel after Milestone 2.

---

## 17. MVP definition of done

The MVP is complete only when the following works on a supported phone and tablet:

1. A student signs in through an invitation.
2. The student creates one study profile.
3. The student adds at least two active target examinations.
4. The application generates one combined session.
5. Each planned problem identifies which targets it supports.
6. A math/geometry problem renders correctly.
7. The student interacts with permitted geometry objects.
8. The student solves on paper and uploads a photo.
9. The AI produces a structured transcript.
10. The student visually corrects text and math.
11. The student confirms the transcript.
12. The AI returns structured step feedback and a score.
13. A valid alternative solution is not rejected merely for differing from references.
14. The student requests a hint.
15. The hint may manipulate curated geometry through validated actions.
16. The student retries.
17. Skill and mistake evidence are recorded.
18. A review is scheduled.
19. The session summary is displayed.
20. Shared progress and per-target coverage update.
21. The next plan reflects the new evidence and balances the active targets.
22. All AI, privacy, content-version, and audit requirements are enforced.
23. The agreed quality gates pass.

The product architecture is:

```text
Curated multi-exam mathematical content
        +
Structured learner state
        +
Deterministic multi-target coaching policy
        +
Frontier multimodal intelligence
        +
Interactive mathematics and geometry UX
```
