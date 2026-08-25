# Privacy and consent action list

## Status and scope

- Milestone: 0 — Scope, governance, and evaluation contract
- Readiness: BLOCKED — qualified review and approvals are `DECISION REQUIRED`
- Privacy owner: DECISION REQUIRED
- Legal reviewer: DECISION REQUIRED
- Security owner: DECISION REQUIRED
- Last updated: 2026-08-25

This is a pre-pilot action register, not legal advice and not a legal conclusion. Qualified reviewers must determine the rules that apply to the approved cohort and operating locations in [`PILOT_SCOPE.md`](../product/PILOT_SCOPE.md). No minors' data may be collected merely because an engineering milestone is technically complete.

## Non-negotiable product constraints

Future implementation must:

- minimize personal data;
- keep provider credentials server-side;
- authorize every user-owned resource;
- use short-lived signed image upload and download URLs;
- validate image type and size;
- remove image metadata according to an approved retention policy;
- keep operational retention separate from optional research retention;
- avoid using student work for model improvement without the approved consent path;
- provide deletion and export behavior approved for the pilot;
- add audit events for sensitive operations;
- record applicable AI provider and processing details without storing hidden chain-of-thought.

These constraints do not resolve the legal basis, retention periods, consent wording, or responsible parties.

## Blocking action register

Every row requires a named owner, dated evidence, and explicit approval or a documented determination that the item is not applicable.

| Action | Required result | Owner | Evidence | Status |
|---|---|---|---|---|
| Determine applicable jurisdictions and rules | Written scope based on cohort location, age, service operator, and data flows | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED |
| Establish lawful basis for each processing purpose | Reviewed mapping covering service delivery, safety, operations, analytics, and optional research | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED |
| Determine age and identity handling | Approved age-screening and identity-minimization approach | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED |
| Determine parent/guardian consent and student assent | Approved applicability decision, collection flow, records, renewal, and withdrawal behavior | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED |
| Review automated educational assessment | Approved notices, uncertainty handling, contest/correction path, and any human-review obligations | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED |
| Inventory personal and sensitive data | Field-level inventory covering accounts, profiles, targets, photos, transcripts, evaluations, logs, and audit events | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED |
| Map processors and data locations | Approved data-flow diagram and processor/subprocessor register | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED |
| Review AI provider processing | Approved terms covering retention, training use, data location, subprocessors, deletion, security, and incident notice | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED |
| Review object storage and hosting | Approved region, access, encryption, retention, backup, and deletion controls | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED |
| Approve image handling | Limits for type/size, signed URL lifetime, malware handling if required, EXIF removal, access, and deletion | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED |
| Approve operational retention schedule | Purpose-specific durations and deletion behavior for all production records | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED |
| Approve optional research retention | Separate opt-in, dataset boundaries, access, withdrawal, de-identification, and destruction plan | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED |
| Define account deletion | Request authentication, deletion scope, exceptions, service level, evidence, and user notice | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED |
| Define data export | Request authentication, export scope/format, secure delivery, service level, and audit behavior | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED |
| Approve participant notices | Age-appropriate student notice plus parent/guardian notice where required | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED |
| Approve consent records | Versioned notice/consent text, actor, timestamp, scope, withdrawal, and re-consent triggers | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED |
| Define authorization and support access | Role matrix, least privilege, support elevation, review cadence, and revocation | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED |
| Define audit events | Sensitive actions, actor, target, timestamp, reason, access, retention, and tamper controls | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED |
| Define incident procedure | Classification, containment, escalation, notification, evidence preservation, and participant support | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED |
| Review security controls and threats | Approved threat model and pilot security checklist | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED |
| Define complaint and correction route | Student/guardian contact, response target, assessment challenge, correction, and escalation | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED |
| Approve pilot data-use boundaries | Written prohibition or authorization for each secondary use | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED |
| Define end-of-pilot disposition | Approved archive, return, anonymization, or deletion action for each data class | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED |

## Required data-flow review

The approved data-flow record must cover at least:

```text
invitation and account
study profile and multiple exam targets
daily plan and interaction events
paper-solution image capture
object storage upload and retrieval
AI transcription and evaluation processing
confirmed transcript and corrections
learner evidence, mistakes, reviews, and rewards
operational logs, model-run metadata, and audit events
support or internal flagged-attempt access
export, deletion, retention expiry, and incident handling
```

For each flow, record purpose, fields, source, recipients, storage location, access roles, retention, deletion behavior, and whether it is necessary or optional.

## Consent and withdrawal requirements

The approved consent design must distinguish:

- participation in the pilot;
- processing required to deliver the coaching service;
- sending work to the selected AI provider;
- optional analytics beyond essential operations;
- optional research use;
- optional model-improvement use, if it is permitted at all.

Bundled consent must not be assumed acceptable. Whether each item requires consent, assent, another basis, or is prohibited is `DECISION REQUIRED` following qualified review.

Withdrawal behavior must define future processing, account access, queued jobs, provider copies, backups, derived evidence, audit records, and previously approved research datasets.

## Image retention decision record

| Item | Approved value |
|---|---|
| Maximum image size and allowed types | DECISION REQUIRED |
| Upload URL lifetime | DECISION REQUIRED |
| Download URL lifetime | DECISION REQUIRED |
| EXIF-removal point and verification | DECISION REQUIRED |
| Original-image operational retention | DECISION REQUIRED |
| Derived-image retention | DECISION REQUIRED |
| Backup retention and deletion propagation | DECISION REQUIRED |
| Internal access roles | DECISION REQUIRED |
| AI provider retention | DECISION REQUIRED |

## Approval and evidence

Milestone 0 does not exit merely because actions are listed. Before approval:

1. Every blocking row must have a named owner and status.
2. Approved policies and notices must be linked as evidence.
3. Product and engineering requirements created by the review must be reflected in the release gates.
4. Any accepted risk must name the accepting authority, rationale, scope, expiry or review date, and mitigation.
5. The Milestone 0 index must be updated with the dated approval.

Final privacy/legal approval: DECISION REQUIRED.
