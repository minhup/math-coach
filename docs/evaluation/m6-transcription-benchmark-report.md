# Milestone 6 transcription benchmark report

## Status

**NOT RUN — OWNER DEFERRED.** No Gemini, OpenAI, or Anthropic network request was made, no API key was
loaded, and the measured-result fields below remain intentionally empty. This report does not approve
any provider for real learner data or production use.

The selected first integration is Google Gemini `gemini-3.5-flash`. Server-configured alternatives
are OpenAI `gpt-5.4-2026-03-05` and Anthropic `claude-sonnet-5`. All implementation contract tests use
hand-authored synthetic response envelopes through `httpx.MockTransport`, never recorded real
provider responses.

## Frozen identities and planned configuration

| Field                         | Value                                                              |
| ----------------------------- | ------------------------------------------------------------------ |
| provider/model                | `google-gemini` / `gemini-3.5-flash`                               |
| prompt version                | `m6-faithful-transcription-v1`                                     |
| prompt SHA-256                | `d487b2f47b769380002a80fa31316bf8e238b3db15f34a7cff0c560473e0ad89` |
| provider schema               | `m6-provider-transcript-v1`                                        |
| application transcript schema | `3.0.0`                                                            |
| fixture manifest SHA-256      | `21c08074e746206f4491cd665ff4897a1164b0aedaf4c7acd8b88423b91aa979` |
| planned run date              | not scheduled                                                      |
| real calls made               | `0`                                                                |
| measured input/output tokens  | not measured                                                       |
| measured latency              | not measured                                                       |
| measured per-run/total cost   | `$0.000000` spent; benchmark measurements unavailable              |

The originally proposed 10-fixture, at-most-20-call Gemini run was explicitly deferred. The final
manifest contains 11 fixtures because warnings/source regions have a dedicated visual fixture. Its
worst-case adapter call count is 22: one initial call plus at most one schema repair for each fixture.
Using the documented planning assumption of at most 10,000 input tokens and the hard 3,000 output
tokens per call, the conservative Gemini estimate is `$0.924000`; the deferred 20-call estimate is
`$0.840000`. Image tokenization is provider-controlled, so these are budget estimates rather than a
guaranteed invoice ceiling. Tax, region, service-tier, and future pricing changes are excluded.

## Repository-owned synthetic fixtures

All images were authored as SVG specifically for this repository, visibly label themselves
`SYNTHETIC TEST FIXTURE — NO PERSON`, and were rendered to 900 × 1200 PNG with FFmpeg 6.1.1 and
librsvg. They contain no real handwriting, learner, examination, personal metadata, or provider
response.

| Fixture                        | Category                             | PNG SHA-256                                                        |
| ------------------------------ | ------------------------------------ | ------------------------------------------------------------------ |
| `clean-handwritten-math`       | clean handwritten mathematics        | `44c8df5c82a95e6cdb82ca099a1914c4061a93380455eaefd068b34c806d2415` |
| `messy-readable-math`          | messy but readable mathematics       | `b13d6f0a3df4d8d6278a755e59b64dd3bbf15679d3ad227b1120fb12c8b4720a` |
| `mixed-vietnamese-math`        | Vietnamese text and mathematics      | `de4f78997cd82e52ca8635cef89957019b575c8bc95979c416d1c33f71ca1046` |
| `cross-outs-insertions`        | cross-outs and insertions            | `a4b4c4722251845cfaf628e0315ba35fdc24d229498fc0f28c56de20c4aa0d11` |
| `correct-standard-solution`    | correct standard solution            | `84e1bacb22c72831415aa99c34858d4b2911c984bf21fde3f12919a773ae810e` |
| `correct-alternative-solution` | correct alternative solution         | `3dfb02009039109e49533b6950021fa17860c96299427d2436ad0c7b953ed4e7` |
| `subtle-error-preserved`       | subtle mathematical error            | `fddd57e0c05200109d980d6e70aad19abfdf3c8fd3c5b7b104eea01144d66280` |
| `incomplete-solution`          | incomplete solution                  | `899cea31cb961554e1e4dc540aad4e601642d69f23f28444abdca73b5bd1430a` |
| `geometry-solution`            | geometry solution                    | `094e308793d351b267d1df07286c3f18ac50282ff6e10269d0c051b6159a02d4` |
| `alternating-text-math`        | alternating text/math on one line    | `924b32743cb72e51af10e2e28623a515f6eed6bbbdcdd94121c83d1d4c973efc` |
| `warnings-source-regions`      | warnings and optional source regions | `f0ba3a02b35369a27c2f0f08a53ba89522a6a4c7f014593ae00e3dd22e0eb592` |

The exact expected flat blocks, warning expectations, error-preservation flag, source filenames, and
provenance are in `services/api/tests/fixtures/transcription/manifest.json`. The benchmark runner
requires every source file and hash-verifies every image before any provider call.

## Deferred measured results

For every fixture, the following fields are **not measured**: validated provider transcript, text
edits required, visual math edits required, ordering errors, preserved mathematical errors,
warning/source-region quality, schema retries/failures, latency, token usage, and cost. No placeholder
transcript or numeric score is fabricated. Consequently there is no benchmark pass/fail result and
no production release claim.

When separately approved, the guarded runner records those fields as JSON:

```bash
make transcription-benchmark BENCHMARK_ARGS='\
  --fixture-root tests/fixtures/transcription \
  --output ../../artifacts/m6-gemini-benchmark.json \
  --approved-provider google-gemini \
  --approved-model gemini-3.5-flash \
  --approved-fixture-count 11 \
  --approved-max-cost-usd 0.924000 \
  --acknowledge-synthetic-only \
  --acknowledge-paid-network-calls'
```

This command is documentation, not authorization to run it. The owner must approve the exact fixture
count and maximum spend again, configure a paid project and server secret, and explicitly request the
network run. The output must then be reviewed and transcribed into this committed report.

## Provider data-handling facts

- Google documents `gemini-3.5-flash` as accepting image input and supporting structured output, at
  `$1.50` per million input tokens and `$9.00` per million output tokens. Paid-service prompts,
  images, and responses are not used to improve Google products, but abuse-monitoring/stateful
  retention conditions still exist; free/unpaid service handling differs. Sources:
  [model](https://ai.google.dev/gemini-api/docs/models/gemini-3.5-flash),
  [pricing](https://ai.google.dev/gemini-api/docs/pricing),
  [ZDR/data handling](https://ai.google.dev/gemini-api/docs/zdr), and
  [terms](https://ai.google.dev/gemini-api/terms).
- OpenAI documents snapshot `gpt-5.4-2026-03-05`, image input, structured outputs, and `$2.50`/`$15`
  per million input/output tokens. API data is not used for training unless opted in; default abuse
  monitoring may retain content for up to 30 days, and Responses application state has separate
  retention behavior. This adapter sends `store: false`, which is not itself a blanket ZDR claim.
  Sources: [model](https://developers.openai.com/api/docs/models/gpt-5.4),
  [image input](https://developers.openai.com/api/docs/guides/images-vision), and
  [data controls](https://developers.openai.com/api/docs/guides/your-data).
- Anthropic documents `claude-sonnet-5`, vision, `$2`/`$10` per million input/output tokens, standard
  retention behavior, and ZDR only for eligible organizations/configurations. This integration does
  not claim such an agreement exists. Sources:
  [model](https://platform.claude.com/docs/en/docs/about-claude/models/whats-new-sonnet-5),
  [pricing](https://platform.claude.com/docs/en/about-claude/pricing), and
  [API retention](https://platform.claude.com/docs/en/manage-claude/api-and-data-retention).

These facts were inspected on 2026-08-28 and can change. Contract terms, billing account status,
region, retention controls, and suitability for minors require owner/legal/privacy review before any
real learner use.

## Known limitations and expected failure modes

- There is no real-provider accuracy, latency, token, cost, warning, region, or error-preservation
  measurement yet.
- Provider structured-output support reduces but does not replace strict application validation.
- Handwriting, Vietnamese notation, cross-outs, insertions, reading order, and malformed mathematics
  remain likely correction points; only a real synthetic benchmark can measure them.
- A schema repair can double calls and cost for one fixture; transport errors receive no automatic
  retry.
- A process/network ambiguity after provider acceptance may leave a processing run and cannot prove
  whether billing occurred.
- No provider retention or production-suitability approval is implied by integration availability.
