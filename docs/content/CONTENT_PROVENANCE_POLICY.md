# Content provenance policy

## Status and purpose

- Milestone: 0 — Scope, governance, and evaluation contract
- Policy status: baseline controls defined; accountable owners and source-policy decisions are `DECISION REQUIRED`
- Content owner: DECISION REQUIRED
- Rights reviewer: DECISION REQUIRED
- Last updated: 2026-08-25

This policy applies to every problem, solution, rubric, hint, concept, image, geometry scene, exam configuration, and derived content item considered for the MVP. Content must not be ingested, redistributed, or published without documented rights and provenance.

## Publication rule

A content version may be released only when:

1. its source and acquisition route are recorded;
2. the right to use, adapt, display, and distribute it for the intended pilot use is documented;
3. required attribution and usage restrictions are captured;
4. the content has passed mathematics, schema, rendering, geometry, and accessibility review where applicable;
5. the released version is immutable and traceable to its review evidence;
6. the content owner has approved publication.

Runtime AI may select or manipulate approved content through validated contracts. It may not publish new content automatically.

## Required provenance record

Every content item must have an immutable version-level provenance record containing:

| Field | Requirement |
|---|---|
| Stable content ID and version | Required |
| Content type | Required |
| Title or external reference | Required |
| Original creator or issuing body | Required when known; absence requires reviewed explanation |
| Original source | Required |
| Source URL, publication, archive, or physical reference | Required as applicable |
| Acquisition date and acquirer | Required |
| Origin examination and cycle | Required for exam-derived problems |
| Rights basis | DECISION REQUIRED from an approved rights vocabulary |
| License or permission evidence | Required; evidence location must be durable |
| Permitted uses and restrictions | Required |
| Attribution text | Required when applicable |
| Adaptation description | Required when the released item differs from the source |
| Translation description and translator | Required when translated |
| Derivation relationships | Required for variants, rubrics, hints, solutions, scenes, and images derived from another item |
| Mathematics reviewer and review date | Required before publication |
| Rights reviewer and review date | Required before publication |
| Publication status and date | Required |
| Withdrawal reason and replacement | Required when withdrawn |

The storage schema and file format for this record will be designed in Milestone 2. That later design must preserve these fields without assuming a problem is relevant to only one exam.

## Source eligibility

The organization must approve a finite source and rights vocabulary before importing content.

| Decision | Approved value |
|---|---|
| Permitted public-domain sources | DECISION REQUIRED |
| Permitted open-license families and versions | DECISION REQUIRED |
| Permission standard for copyrighted examination material | DECISION REQUIRED |
| Policy for student- or teacher-contributed content | DECISION REQUIRED |
| Policy for commissioned original content | DECISION REQUIRED |
| Policy for AI-assisted drafting | DECISION REQUIRED |
| Sources or licenses that are prohibited | DECISION REQUIRED |
| Required attribution placement | DECISION REQUIRED |
| Jurisdiction-specific restrictions | DECISION REQUIRED |

An available webpage, scan, social post, textbook page, or previous examination is not automatically authorized for ingestion or redistribution.

## AI-assisted content

AI assistance does not establish provenance, ownership, correctness, or publication rights. If AI is used during drafting or transformation, the record must identify:

- the human initiating and reviewing the work;
- the source material supplied to the provider;
- provider and model snapshot;
- prompt or workflow version when retained by policy;
- the nature of the generated or transformed material;
- the mathematical and rights review performed;
- whether provider terms permit the intended use.

Whether AI-assisted content is allowed for each content type is DECISION REQUIRED. AI-generated content may not bypass human publication review.

## Review requirements by content type

| Content type | Minimum review |
|---|---|
| Problem statement | Source/rights, mathematical accuracy, typed-content schema, rendering, exam relevance |
| Reference solution | Mathematical accuracy, method label, non-exhaustive-reference wording |
| Rubric | Scoring consistency, skill links, alternative-method compatibility |
| Hint | Mathematical accuracy, progressive disclosure, full-solution disclosure flag |
| Concept | Mathematical accuracy, scope, rendering, accessibility |
| Geometry scene | Source/rights, mathematical construction, schema/action validation, deterministic render, fallback image, accessibility description |
| Image or media | Source/rights, attribution, metadata removal, accessibility text, storage policy |
| Exam-skill weights | Expert owner, version, source note, consistency with the approved exam cycle |
| Problem-exam relevance | Expert owner, finite relevance scale, rationale, supported exam cycles |

Reference solutions are non-exhaustive. Review must not encode one stored solution as the only valid mathematical method.

## Versioning and corrections

- Content source files are version-controlled YAML or JSON and schema-validated before import.
- Published attempts must reference immutable content versions.
- Correcting published content creates a new version; it must not rewrite the version referenced by an attempt.
- Provenance changes create a new reviewed provenance record linked to the affected content version.
- Withdrawn content remains traceable for historical attempts but cannot be selected for new work.
- A rights dispute or material mathematical error triggers immediate selection blocking and review according to an approved incident procedure.

The exact withdrawal authority, response times, and participant-notification rules are DECISION REQUIRED.

## Roles and separation of duties

| Role | Responsibility | Named owner |
|---|---|---|
| Contributor | Prepares content and provenance evidence | DECISION REQUIRED |
| Mathematics reviewer | Verifies correctness, alternatives, scoring, and pedagogy | DECISION REQUIRED |
| Rights reviewer | Verifies permission, license, attribution, and restrictions | DECISION REQUIRED |
| Publisher | Confirms all required reviews before changing publication status | DECISION REQUIRED |
| Incident owner | Blocks or withdraws disputed or unsafe content | DECISION REQUIRED |

Whether one person may hold more than one role, and for which content risk levels, is DECISION REQUIRED.

## Evidence storage and retention

Rights and approval evidence must be durable, access-controlled, and linked from the content record. Do not commit secrets, unnecessary personal data, or restricted source material to Git merely to preserve evidence.

| Decision | Approved value |
|---|---|
| Evidence system of record | DECISION REQUIRED |
| Evidence access roles | DECISION REQUIRED |
| Evidence retention period | DECISION REQUIRED |
| Treatment of expiring permissions | DECISION REQUIRED |
| Audit/review cadence | DECISION REQUIRED |

## Milestone 0 exit evidence

This policy satisfies its Milestone 0 gate only after:

- source and rights vocabularies are approved;
- content and rights owners are named;
- evidence storage and retention are approved;
- publication and withdrawal authority are approved;
- at least one representative content package has been walked through the policy and gaps are recorded;
- approval is dated and linked from the Milestone 0 index.

Final content-provenance approval: DECISION REQUIRED.
