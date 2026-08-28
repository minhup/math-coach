# Multimodal transcription architecture

Milestone 6 replaces the Milestone 5 in-memory mock transcript with an authenticated, durable,
provider-shaped transcription path. It does not add production grading. The existing evaluation,
hint, retry, and concept flow remains visibly deterministic and synthetic.

## Ownership and request flow

The browser sends only an owned upload ID and a UUID idempotency key to
`POST /api/v1/attempts/{attempt_id}/transcribe`. It cannot select a provider, model, prompt, schema,
retry policy, or outcome. FastAPI authenticates the invitation session, loads the owned attempt and
owned ready upload, locks creation of the attempt/upload association, and reads at most the existing
10 MB upload limit from the internal object-storage endpoint. The detected PNG, JPEG, or WebP magic
must match the object metadata that was verified during upload completion.

The attempt remains pinned to its existing immutable `problem_version_id`. The service passes the
exact stored problem statement as context and the verified bytes to one configured server adapter.
It never sends a signed browser/object-storage URL to a provider. Ordinary HTTP is sufficient: the
current operation returns one complete result and has no one-way progress events that justify SSE.

The response is not persisted or rendered until the complete provider payload passes the strict
provider schema and is converted to application-owned types. A valid uncertainty result has warnings
and no transcript. Failures never create fallback blocks.

## Provider adapter

`StrictTranscriptionProvider` is the only provider seam. It has one `transcribe` operation and no
evaluation, grading, hint, workflow, or generic completion methods. Provider request/envelope types
remain inside `app/transcription`; service code receives only `ProviderResult` and validates that its
identity exactly matches the configured adapter.

The owner-approved server choices are:

| Setting     | Stored provider                        | Exact model                   | Pricing identity                   |
| ----------- | -------------------------------------- | ----------------------------- | ---------------------------------- |
| `gemini`    | `google-gemini`                        | `gemini-3.5-flash-lite`       | `gemini-3.5-flash-lite-2026-08-28` |
| `gemini`    | `google-gemini`                        | `gemini-3.5-flash`            | `gemini-3.5-flash-2026-08-27`      |
| `openai`    | `openai`                               | `gpt-5.4-2026-03-05`          | `gpt-5.4-2026-08-27`               |
| `anthropic` | `anthropic`                            | `claude-sonnet-5`             | `claude-sonnet-5-2026-08-27`       |
| `fake`      | `application-owned-deterministic-fake` | `m6-transcription-fixture-v1` | `fake-zero-v1`                     |

Flash-Lite is the first lower-cost Gemini configuration and Flash remains an exact server option.
The deterministic fake remains the development/test default and traverses the same API, service,
persistence, and frontend boundaries. Production startup rejects fake mode. Exact model validation
rejects other Gemini IDs, aliases, or browser overrides. Self-hosted, DeepSeek, Qwen, and generalized
model configuration are deferred to a later change.

The adapters use direct `httpx==0.28.1` calls instead of provider SDKs. Every request caps visible
output at 3,000 tokens. OpenAI and Anthropic receive the full provider JSON Schema. Gemini receives
application-owned minimal schema guidance containing only its live-validated core object, array,
string, number, integer, enum, properties, required, and items vocabulary; sending Pydantic's richer
union and constraint schema caused a pre-generation HTTP 400 from Flash-Lite. The Gemini guidance is
intentionally broader for conditional text/math and ready/uncertain fields, but the response still
passes through the same strict authoritative Pydantic discriminated unions before persistence or UI
use. OpenAI uses the Responses API with
base64 image input, `store: false`, and reasoning effort `none`. Anthropic disables Sonnet 5 adaptive
thinking for this transcription-only request. No adapter retains or exposes raw error bodies, raw
responses, internal reasoning, or provider-supplied identity metadata.

The reviewable prompt is `m6-faithful-transcription-v1`, SHA-256
`d487b2f47b769380002a80fa31316bf8e238b3db15f34a7cff0c560473e0ad89`. It requires a faithful flat
transcription, explicitly preserves mathematical errors, and forbids solving, grading, normalization,
Markdown, HTML, URLs, executable code, and reasoning groups. Provider schema
`m6-provider-transcript-v1` is paired with application transcript schema `3.0.0`.

## Authoritative transcript

`TranscriptDocument` remains one canonical ordered array. Text and math are the only block variants;
IDs are non-empty and unique. Provider positions become stable application IDs derived from the
attempt asset. Mathematics is stored as typed math source but edited visually through MathLive; a
KaTeX failure continues to show the existing source-free correctable placeholder.

Optional source regions use normalized top-left `x`, `y`, `width`, and `height`, are finite, remain
inside the image, and carry the application-stamped attempt asset ID. The correction screen exposes
regions through 44 px keyboard/touch controls and overlays the selected region on the owned source
image. Warnings have only these finite application messages:

- `low_confidence_text`, `low_confidence_math`;
- `ambiguous_cross_out`, `ambiguous_insertion`;
- `ordering_uncertain`, `source_region_unavailable`.

Provider warning prose is not accepted. Unknown fields, variants, enums, HTML/Markdown/URLs,
executable content, empty ready documents, invalid region bounds, or missing block references fail
Pydantic validation. Validation failure causes exactly one schema-repair call; a second failure is
terminal. Transport failures are never automatically retried.

Learner correction may edit text/math values, reorder or remove existing blocks, and insert new
blocks. Existing block type and source-region provenance cannot change, new blocks cannot claim a
source region, and warnings may only be removed—not invented. Saving creates a new immutable version.
The browser compares typed transcript fields rather than serialized JSON key order: an unchanged
provider document confirms version 1 directly, while an actual content edit creates a learner
version. Once confirmed, correction is rejected. Confirmation stores the exact version ID and
canonical SHA-256, and repeating the same confirmation is idempotent.

## Persistence and API

Migration `20260827_0003` adds only:

- `attempt_assets`: immutable attempt/upload/content-hash links;
- `prompt_versions`: immutable prompt text, hash, version, and schema identity;
- `ai_model_runs`: processing-to-terminal run state and validated metadata;
- `transcript_versions`: immutable provider/learner documents, lineage, version, and hash;
- `transcript_confirmations`: one immutable exact version/hash selection per attempt.

Image bytes remain in object storage. JSONB contains only validated application transcript documents
or finite warning data. Model runs record provider, exact model, prompt/schema/pricing identity,
schema attempts, latency, input/output tokens, calculated cost, safe error code, and timestamps.
Run identity is immutable; a database trigger permits only one transition from processing to a
terminal status. Separate append-only triggers protect assets, prompts, transcript versions, and
confirmations.

The partial `uq_ai_model_runs_asset_processing` index enforces one in-flight run per attempt asset.
`ix_ai_model_runs_asset_fingerprint_created` supports completed-request replay, and
`ix_transcript_versions_source_run_version` supports a run's version lookup. Existing unique
`(attempt_id, version)` ordering supports latest-version reads. No speculative index or Milestone
7–9 table is added.

The authenticated API is:

```text
POST /api/v1/attempts/{attempt_id}/transcribe
GET  /api/v1/attempts/{attempt_id}/transcription
POST /api/v1/attempts/{attempt_id}/transcripts
POST /api/v1/attempts/{attempt_id}/confirm-transcript
POST /api/v1/uploads/{upload_id}/download-url
POST /api/v1/attempts/{attempt_id}/mock-evaluation
```

The last endpoint now accepts only `confirmedTranscriptVersionId`; the backend loads the exact
confirmed durable version. It remains a deterministic synthetic M5 evaluator and never becomes
production grading merely because its input came from a real transcription adapter.

## Idempotency, concurrency, and failure states

A repeated idempotency key returns its terminal run or reports the existing processing run without a
second call. A different key for the same completed asset/configuration fingerprint replays the
completed result. A different key while processing receives `transcription_in_progress`; it cannot
start a second paid run. A new key may retry only a prior retryable failure. Successful, uncertain,
permanent, and invalid-schema outcomes are terminal for that asset/configuration fingerprint; a new
verified upload creates a distinct asset.

Stable safe states are `processing`, `ready`, `uncertain`, `retryable_failure`, `permanent_failure`,
and `invalid_schema`. Timeout, rate limit, and transport errors are retryable. Invalid media and
provider rejection are permanent. Empty/malformed structured output after one repair is terminal
invalid schema. The browser renders no transcript for any failure or uncertainty state.

A process crash after a provider accepts a request but before the terminal database commit can leave
a processing row. M6 does not guess whether that paid call completed and does not automatically
launch another. Operational stale-run recovery requires a later owner-approved policy.

## Privacy, retention, and configuration

Only clearly synthetic, non-personal, repository-owned fixtures may be sent during development or
benchmarking. Real student/minor data is prohibited until separate provider, retention, consent, and
production-suitability approvals exist. Provider keys are server-only `SecretStr` settings and must
come from a local untracked `.env` or deployment secret manager—never a `NEXT_PUBLIC_` variable,
browser request, signed URL, log, commit, or chat message.

Official documentation does not justify a blanket zero-retention claim. Paid Gemini API content is
not used to improve Google products, but abuse-monitoring/stateful-feature caveats still apply;
OpenAI documents default abuse-monitoring and Responses application-state retention with separately
approved controls; Anthropic documents standard retention and separately arranged ZDR. Exact facts
and sources are recorded in the [M6 benchmark report](../evaluation/m6-transcription-benchmark-report.md).

Provider-run, transcript, confirmation, upload, and object retention periods remain an owner privacy
decision. M6 preserves these audit records and does not invent automatic deletion. Downgrading to M5
drops every M6 record and is materially destructive; it requires stopping M6 writes, exporting any
required audit data, taking a backup, and obtaining owner authorization. Attempts, uploads, profiles,
targets, and immutable content versions survive the downgrade.

## Benchmark boundary

`make transcription-benchmark BENCHMARK_ARGS='…'` is deliberately outside `make check`. It refuses
fake mode, mismatched provider/model/fixture count, missing synthetic/paid acknowledgements, or a
cost approval below its conservative estimate. The adapter itself limits schema attempts to two and
output tokens to 3,000. The user has deferred the real benchmark, so no network call or measured
provider result is part of Milestone 6 handoff; see the committed report for the exact deferred state.
