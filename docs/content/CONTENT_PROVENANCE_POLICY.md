# Content provenance policy

## Status and purpose

- Milestone: 0 — Internal MVP direction and deferred-gate register
- Internal implementation: NOT BLOCKED when using original synthetic fixtures
- Real-content publication: DEFERRED — source-policy decisions are `DECISION REQUIRED`
- Decision authority: Project owner
- Rights reviewer: DECISION REQUIRED
- Last updated: 2026-08-25

This policy applies to every real problem, solution, rubric, hint, concept, image, geometry scene, exam configuration, and derived content item considered for import or publication. It does not block internal schema and UI development with clearly labeled original synthetic fixtures. Third-party content must not be ingested, redistributed, or published without documented rights and provenance.

## Publication rule

A content version may be released only when:

1. its source and acquisition route are recorded;
2. the right to use, adapt, display, and distribute it for the intended pilot use is documented;
3. required attribution and usage restrictions are captured;
4. the content has passed mathematics, schema, rendering, geometry, and accessibility review where applicable;
5. the released version is immutable and traceable to its review evidence;
6. the project owner has confirmed publication after the required reviews.

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

The project owner must approve a finite source and rights vocabulary before importing real third-party content.

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
| Exam-skill weights | Expert review evidence, version, source note, consistency with the approved exam cycle |
| Problem-exam relevance | Expert review evidence, finite relevance scale, rationale, supported exam cycles |

Reference solutions are non-exhaustive. Review must not encode one stored solution as the only valid mathematical method.

## Versioning and corrections

- Content source files are version-controlled YAML or JSON and schema-validated before import.
- Published attempts must reference immutable content versions.
- Correcting published content creates a new version; it must not rewrite the version referenced by an attempt.
- Provenance changes create a new reviewed provenance record linked to the affected content version.
- Withdrawn content remains traceable for historical attempts but cannot be selected for new work.
- A rights dispute or material mathematical error triggers immediate selection blocking and review according to an approved incident procedure.

The exact withdrawal authority, response times, and participant-notification rules are DECISION REQUIRED.

## Review functions

| Function | Responsibility |
|---|---|
| Contribution | Prepare content and provenance evidence |
| Mathematics review | Verify correctness, alternatives, scoring, and pedagogy |
| Rights review | Verify permission, license, attribution, and restrictions |
| Publication | Confirm all required reviews before changing publication status |
| Incident handling | Block or withdraw disputed or unsafe content |

The project owner may perform or commission these functions during the MVP. Each published item must retain the applicable review evidence. Multi-person approval governance is deferred until product-release preparation.

## Evidence storage and retention

Rights and approval evidence must be durable, access-controlled, and linked from the content record. Do not commit secrets, unnecessary personal data, or restricted source material to Git merely to preserve evidence.

| Decision | Approved value |
|---|---|
| Evidence system of record | DECISION REQUIRED |
| Evidence access roles | DECISION REQUIRED |
| Evidence retention period | DECISION REQUIRED |
| Treatment of expiring permissions | DECISION REQUIRED |
| Audit/review cadence | DECISION REQUIRED |

## Pre-publication gate

Before real third-party content is imported or published:

- source and rights vocabularies are approved;
- required mathematics and rights review evidence is available;
- evidence storage and retention are approved;
- the project owner has confirmed publication and withdrawal rules;
- at least one representative content package has been walked through the policy and gaps are recorded;
- approval is dated and linked from the Milestone 0 index.

Real-content publication confirmation: DEFERRED.
