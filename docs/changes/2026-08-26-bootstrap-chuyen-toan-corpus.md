# Bootstrap Vietnamese Chuyen Toan research corpus

## Metadata

- Status: complete
- Owner: Codex
- Branch: `chore/bootstrap-chuyen-toan-corpus`
- Base commit: `f899a11614784d21b365ad31ff271b7be7e0385c`
- Related milestone: Pre-Milestone 2 data and content research
- Related issue/ticket: None
- Started: 2026-08-26
- Last updated: 2026-08-27

## Context

The repository has product research describing five Vietnamese competitive Grade-10 Mathematics
entrance-exam families, but it has no reproducible research-corpus inventory, acquisition manifests,
raw-data storage convention, extraction pipeline, or data-quality reports. This change establishes
the evidence-preserving research layer needed to determine what material exists before any exam is
selected for production content.

Repository policy currently leaves the real-content source/rights vocabulary and evidence system as
`DECISION REQUIRED` and has no configured Git LFS or external corpus object store. The project owner
subsequently authorized processing all obtainable data for this research pass without resolving
rights. Accordingly, every unstated right remains `unknown` and all use is research-only. The owner
later directed that the entire `data/` tree, including manifests and reports, remain local and
ignored for now; Git contains only the reproducible tooling, tests, and this execution record.

## Goal

Create a deterministic, rerunnable corpus toolchain and local inventory for PTNK, TP.HCM So
Chuyen, KHTN, HNUE, and Ha Noi So Chuyen, then extend the same research corpus with the owner's
expanded global registry. Preserve source provenance and uncertainty, validate every eventual raw
object by bytes and metadata, generate inventory/quality/gap/ingestion reports, and define a small
research-only problem/annotation pilot without treating it as reviewed production content. Maintain
one durable acquisition-status ledger that reports logical sets separately from raw files and can be
regenerated after every later download wave.

## Non-goals

- Change application, API, database, or student-facing behavior.
- Select the production examination set.
- Circumvent authentication, paywalls, robots restrictions, or source terms.
- Publish or redistribute material whose permitted use is not documented.
- Add RAG, vector search, OCR infrastructure, model training, production geometry scenes, or
  large-scale AI annotation.
- Infer unsupported duration, score, round, school, solution authority, or difficulty precision.

## User-visible behavior

None. This is a research-data and operator-tooling change.

## Current-state findings

- `origin/main` is `88b77350948c5d190208457bf8c8bac5ca5952ee`; this branch was created
  directly from that commit after `git fetch origin --prune`.
- Local `main` has one unrelated unpushed commit, `16e7b3a`, containing the in-progress Milestone 2
  ChangePlan. It remains preserved on `main` and is not part of this branch.
- The supplied workbook, product memo, and prompt copy are untracked owner files below
  `docs/research/`; they were read as inputs and will not be modified or staged implicitly.
- All six workbook sheets were inspected: Executive Summary, Exam Systems, Competitors, Product
  Gaps, MVP Recommendation, and Sources. The workbook identifies official school/university and
  government sources, community GitHub archives, commercial tutoring providers, and news sources.
- No `data/` corpus structure or corpus scripts/tests currently exist.
- `.gitattributes` is absent and `git lfs track` lists no patterns. Git LFS is installed locally, but
  repository/server policy and quota are not approved.
- The content boundary currently rejects publishable content packages, while the provenance policy
  states that third-party content must not be ingested without documented rights and provenance.
  The permitted source/rights vocabulary, rights reviewer, and evidence system are all unresolved.
- The root Python toolchain is the Python 3.12 uv project in `services/api`; Ruff covers `scripts/`.
  Poppler (`pdfinfo`, `pdftotext`, and `pdftoppm`), `file`, and `curl` are available. `openpyxl` is not
  installed, so workbook inventory parsing will use a small standard-library XLSX reader rather than
  add an application dependency.
- Network-dependent tests must remain outside the normal suite; local byte fixtures will cover
  downloader and extraction behavior.

## Design

### Repository layout

Use a research-only tree separate from production `content/`:

```text
data/corpus/
  manifests/
    sources.csv
    exams.csv
    files.csv
    missing_data.csv
  raw/<exam-family>/<year>/
  normalized/<exam-family>/
  extracted/<exam-family>/
  annotations/
    annotation_schema.json
    pilot_problems.jsonl
  reports/
    authoritative_source_findings.md
    corpus_inventory.md
    source_quality.md
    missing_years.md
    ingestion_report.md
scripts/corpus/
tests/corpus/
```

Raw objects are immutable and derived artifacts never replace them. The three cache roots contain a
tracked `.gitignore`; their local family/year contents are intentionally not committed.

### Source and acquisition boundary

The workbook-derived source inventory is created before any download. Each source has a stable ID,
original URL, organization, source category, official status, intended acquisition role, explicit
rights statement when present, and conservative use flags. Unstated rights remain `unknown`.

Acquisition priority is authoritative source, strong archive, then commercial/reference-only.
Commercial sources are discovery/research references only unless separately permitted. HTTP
responses are checked for status, final URL, declared and detected MIME, and size before atomic
placement. Provenance records survive duplicate-byte detection even when physical storage is shared.

### Pipeline

```text
workbook/source research -> source inventory -> bounded download plan -> download/checksum
  -> classification/metadata -> normalization/extraction -> validation -> manifests/reports
```

Each stage accepts explicit paths, writes deterministically, and is idempotent. Network behavior is
mocked in tests. Failures and ambiguity become manifest/report rows instead of being discarded.

### Manifest and annotation boundaries

CSV schemas implement the requested source, file, exam, and missing-data fields. Unknown evidence is
empty/null or the literal controlled value `unknown`, as appropriate. Deterministic IDs derive from
normalized evidence fields, not filenames. Difficulty provenance distinguishes unknown,
AI-suggested, expert-verified, and empirically calibrated values. Pilot problem and annotation records
retain source locations and field-level provenance; AI suggestions are never marked verified.

### Storage and rights boundary

The project owner authorized research processing while asking that rights work be deferred. No
license or production-use conclusion is inferred: `rights_status=unknown` remains explicit, and the
safe-for-redistribution/production fields remain `unknown`. Because the bounded raw cache is about
233.67 MiB and the repository has neither LFS configuration nor an object-store contract, the owner
directed that `/data/` be ignored in full. Raw bytes, manifests, reports, annotations, native text,
and normalized derivatives remain available locally but are absent from the pushed Git history. A
later durable-storage and data-versioning choice remains a separate team decision.

### Dependencies

No new runtime or development dependency is planned. Standard-library Python handles CSV, hashing,
HTTP, JSON, and the limited XLSX ZIP/XML source extraction. Existing system `file` and Poppler tools
perform MIME/PDF checks when available; their absence produces an explicit capability/error result.

## Multi-exam impact

This change researches five exam families and never models a student target. A problem may have
multiple explicit `exam_relevance` entries in the annotation proposal. No study profile, target,
exam-specific progress, shared learner state, or daily-plan behavior changes.

## Files and components

Owned by this branch:

- `docs/changes/2026-08-26-bootstrap-chuyen-toan-corpus.md` - execution record.
- `scripts/corpus/**` - reproducible inventory, acquisition, validation, extraction, manifest, and
  reporting commands.
- `tests/corpus/**` - isolated local-fixture tests.
- `.gitignore` - ignores `/data/` in full.

Generated and acquired outputs remain local under `data/corpus/**`; they are owned research outputs
for operational purposes but are not committed or pushed.

The supplied untracked `docs/research/**` inputs are not owned and will not be modified. The active
Milestone 2 branch owns production `content/`, API/database contracts, root command configuration,
and shared application files; this change will not edit those paths.

## API and schema changes

No application API or production content schema changes. New research-only CSV/JSON field contracts
are documented and validated by corpus scripts.

## Database and migration

None. Research manifests and derived artifacts are filesystem data only.

## Security and privacy

- Do not store secrets, credentials, signed URLs, cookies, or personal/student data.
- Do not bypass access controls or automate against prohibited sources.
- Bound response size and timeouts; reject unsafe redirects/schemes and HTML masquerading as files.
- Preserve third-party bytes only under the approved storage/rights policy.
- Treat all extracted/OCR/AI-derived text as untrusted research material, never production content.

## Test plan

### Unit

- URL normalization, domain/source classification, and workbook URL extraction.
- Deterministic source/file/exam/problem IDs and metadata normalization.
- Streaming SHA-256, duplicate-byte detection, and idempotent manifest updates.
- Manifest required fields, controlled values, missing metadata, duplicate IDs, and year mismatch.
- Download success/failure handling, response-size limits, MIME/header/signature mismatches, zero-byte
  and malformed-file rejection using a local HTTP fixture.
- Fixture-based born-digital PDF/image extraction and malformed PDF handling.
- Question/answer classification and missing-row/local-file checks.

### Integration

- Run the complete pipeline twice on local fixtures and prove byte-identical manifests/reports with
  no duplicate rows or raw overwrite.
- Run the expanded P0/P0X pipeline twice against the local cache and prove byte-identical registry
  manifests and acquisition ledger with zero network downloads on the second pass.

### Acceptance criteria

- Every workbook exam-related URL appears once in the initial source inventory with original
  provenance and category.
- Five families have an approximately ten-cycle availability matrix based only on cited evidence.
- Every acquired raw file has a manifest row and SHA-256; every failure/ambiguity has a missing-data
  row.
- Validation detects all requested failure classes and reports PDF page/text properties where
  practical.
- Reports distinguish official, archive, commercial, and uncertain sources and expose gaps.
- The pilot contains only source-backed normalized records and separates source facts, expert labels,
  and AI-suggested unverified labels.
- No raw/derived conflation, unsupported metadata inference, application-code change, or silent
  ambiguity is present.

## Manual QA

1. Inspect the generated source inventory against all workbook sheets and verify every URL/category.
2. Run each corpus command with `--help` and then against the local fixture corpus.
3. Run the fixture pipeline twice and compare manifests/reports.
4. Spot-check representative downloaded PDFs with `pdfinfo`, native text extraction, rendered page
   images, and the source page in a browser.
5. Confirm raw checksums do not change after derived extraction and reruns.

## Rollout and rollback

There is no application rollout. Tooling changes roll back by reverting their commits. Local data
files are preserved independently of Git and are never deleted by ordinary reruns. If approved for
versioning later, they must follow a separately selected external/LFS policy.

## Branch and commit plan

1. `chore: ignore local corpus data`
2. `feat: add corpus processing tooling`
3. `docs: document corpus processing workflow`

No commit includes any path below `data/`; the unpushed branch history is rewritten before merge so
data snapshots are not merely deleted at the tip while remaining reachable in pushed history.

## Conflict coordination

This branch owns only the paths listed above. It deliberately avoids production `content/`, the API,
database/migrations, root Makefile, and generated client contracts owned by the active Milestone 2
work. Integration order is independent for tooling-only research; any future promotion into
production content must follow after Milestone 2 and a separately approved rights/schema change.

## Risks

- Historical files may be copyrighted without an explicit reuse license. Mitigation: record unknown
  rights and prohibit redistribution/production promotion in this research pass.
- A ten-cycle/five-family corpus may be too large for ordinary Git. Mitigation: inventory sizes first
  and obtain an explicit LFS/object-store/manifest-only decision.
- Community filenames may misidentify year, round, or answer status. Mitigation: keep archive
  provenance, cross-check with official evidence, and expose ambiguity.
- Official sites may be incomplete, unstable, or block automation. Mitigation: bounded respectful
  access, no bypass, recorded failures, and archive discovery only.
- PDF text extraction can corrupt mathematical notation. Mitigation: retain originals, record
  extraction method/quality, and require later expert normalization.
- Concurrent Milestone 2 work may change the future production schema. Mitigation: keep this corpus
  contract research-only and avoid shared application/schema files.

## Progress

- [x] Repository inspected
- [x] Plan reviewed
- [x] Branch created from current main
- [x] Tests written or updated
- [x] Implementation complete
- [x] Documentation updated
- [x] Relevant checks pass
- [x] Diff reviewed
- [x] Branch rebased on current main
- [x] Conflict resolution re-tested
- [x] Handoff summary written

### Expanded-registry continuation

- [x] All seven workbook sheets and 65 master-queue rows inventoried
- [x] All 155 URL-role provenance rows recorded
- [x] P0/P0X candidates discovered and bounded by recommended scope
- [x] Selected expanded candidates downloaded, checksummed, and validated
- [x] Native extraction and normalized sidecars generated locally
- [x] One 65-collection downloaded/missing ledger generated
- [x] Expanded pipeline rerun proved byte-identical
- [x] New local-fixture tests and repository checks pass
- [x] Expanded continuation committed and rebased on latest `origin/main`
- [x] Final expanded handoff recorded

### Set-level reconciliation continuation

- [x] Reinspect repository rules, the active plan, corpus documentation, pipeline code, and tests
- [x] Confirm the existing branch remains based on current `origin/main`
- [x] Add deterministic set/component manifests without treating bundles or landing pages as sets
- [x] Decompose and visually verify the JBMO 2012-2025 bundle
- [x] Classify and group Vietnamese multi-image question/answer artifacts conservatively
- [x] Import owner-provided manual files through an explicit provenance-preserving path
- [x] Attempt the bounded high-priority official-source recovery list
- [x] Regenerate set, solution, ambiguity, and missing-cycle statistics
- [x] Add fixture tests for bundle decomposition, page grouping, manual import, and rerun idempotence
- [x] Run corpus and repository checks, review the diff, rebase, and record the handoff

Acceptance criteria for this continuation:

- The reported complete-set total excludes bundles, HTML snapshots, partial shortlist images, and
  other proxy IDs.
- Every represented set has explicit component rows identifying its question, solution, or
  unresolved artifacts; multi-page components preserve page order and source-file provenance.
- The JBMO bundle contributes annual sets only where page-level evidence supports year, artifact
  role, and page boundaries. Existing official 2022/2024 files remain canonical provenance anchors.
- Automated classification never silently promotes an ambiguous image to a question or answer;
  confidence/evidence and unresolved status remain visible.
- Owner-provided files are never altered or moved in place, and are not imported without a source
  or explicit `source_unknown` provenance record.
- A complete rerun produces identical manifests and reports without duplicate sets or components.
- Network-dependent recovery remains outside the normal test suite and every failed attempt is
  recorded.

Files additionally owned by this continuation:

- `data/corpus/manifests/problem_sets.csv` - one reconciled row per distinct set.
- `data/corpus/manifests/set_components.csv` - ordered file/page components and companion roles.
- `data/corpus/manifests/manual_imports.csv` - explicit owner-provided input provenance.
- `data/corpus/reports/set_reconciliation.md` - downloaded, solution-covered, bundled, and missing
  counts generated from reconciled manifests.
- `data/corpus/reports/reconciliation_source_recovery.md` - primary-source recovery evidence.
- `scripts/corpus/reconcile_sets.py` and focused helpers/tests - deterministic reconciliation.

This continuation still does not own application code, production `content/`, API/database schemas,
the untracked `data/test_problem.jpeg`, or the original files below `docs/research/` and
`data/manual_downloaded/`.

### Question-only core recovery continuation

- [x] Keep the existing corpus branch and reopen this ChangePlan
- [x] Research nine missing core question papers using primary sources
- [x] Seek an accessible replacement for the blocked HNUE 2023 question paper
- [x] Source-cross-check the JBMO 2013 and 2020 bundle identities
- [x] Download and validate only verified question papers; do not seek solutions
- [x] Regenerate set/component manifests and question-coverage reports
- [x] Prove rerun idempotence, run checks, rebase, and record the handoff

Acceptance criteria for this continuation:

- No solution-specific discovery or acquisition target is pursued, including for the blocked PTNK
  2025 and HNUE 2023 answer files. If an immutable question-source compilation incidentally contains
  worked-solution pages, preserve its original bytes but do not map or count those pages.
- Only actual specialist-Mathematics question papers with supported family/year identity enter the
  eligible set count; reference, common-Math, and sample papers remain excluded.
- Ordinary public access only is used. Authentication, anti-bot controls, and owner permissions are
  not bypassed.
- Every recovered question retains its direct URL, landing provenance, source class, retrieval time,
  MIME, size, SHA-256, and local path.
- Source cross-checking may strengthen an identity status, but it must not be presented as
  mathematics-expert verification.
- Missing and blocked targets remain explicit in the generated question-coverage summary.

Additional files owned by this continuation:

- `data/corpus/reports/core_question_recovery_2026-08-27.md` - primary-source search evidence.
- Focused additions to existing acquisition/file/set/component manifests and reports.
- Focused corpus-script/tests changes only if required for deterministic question-only ingestion.

## Decisions

- 2026-08-27: Before merge, the project owner directed that no `data/` content be committed and that
  the directory be ignored for now. Rewrite the unpushed corpus branch in place against
  `origin/main`, retain all local files, and ensure the pushed commit graph contains no `data/`
  paths. This supersedes the earlier manifest-only Git policy.
- 2026-08-27: Represent a mixed immutable source as `question_solution_bundle`, set both raw
  presence flags truthfully, and map only reviewed question page ranges. The raw file is not an
  answer reference and does not create a solution component during this question-only pass.
- 2026-08-27: Store the KHTN multi-year compilation once under its 2017 storage anchor and map page
  20 to KHTN 2017 and page 22 to KHTN 2018. A shared raw object may support several cycle-specific
  question components without duplicating bytes or sets.
- 2026-08-27: Use workbook-authorized TOANMATH and OnThi123 mirrors only after bounded first-party
  research found no accessible actual-paper binaries. Mirror status stays third-party even where
  the visible reproduced header establishes the issuing authority and cycle.
- 2026-08-27: The project owner explicitly deferred solution seeking. This continuation covers only
  missing/blocked question papers and source-based identity checks; solution statistics remain
  visible but are not an acquisition target.
- 2026-08-27: The project owner asked to execute the previously proposed set-level reconciliation
  on the existing corpus branch and reiterated that no additional branch should be created.
- 2026-08-27: Distinguish the generated operational count (74 IDs) from complete year-level sets.
  The reconciliation baseline is 72 represented annual sets with four confirmed solution
  companions; two JBMO shortlist/proxy IDs remain excluded until decomposed or reclassified.
- 2026-08-27: Treat `data/manual_downloaded/` as owner-provided immutable input. Inspect it, but do
  not move, overwrite, stage, or silently invent its download URL.
- 2026-08-27: Model one paper as a problem set and every file, alternate scan, solution, blocked
  source, or bundle page range as a component. This replaces the earlier operational proxy count.
- 2026-08-27: Import the owner-provided Lam Sơn compilation byte-identically into the ignored raw
  cache and record the missing exact download URL explicitly. The supplied original remains
  untouched and untracked.
- 2026-08-27: Treat the 21 publisher-claimed Lam Sơn Chuyên Toán papers as research identities, not
  expert-verified facts. Preserve 29 adjacent/mock/survey papers outside the eligible actual count.
- 2026-08-27: Add only three first-party JBMO files recovered through ordinary access. Keep the
  remaining official-source targets as blocked, landing-only, non-actual, or not-located evidence.

- 2026-08-26: The project owner directed the expanded global acquisition to remain on this existing
  corpus branch as a special data-processing continuation. No additional Git branch or ChangePlan
  will be created.
- 2026-08-26: Import all 65 logical collections and 99 unique queue URLs from
  `global_math_problem_source_registry_expanded.xlsx`, but follow the workbook's own acquisition
  waves. The first bounded run selects the 19 P0/P0X Vietnam-core and JBMO-core collections; every
  later-wave collection remains visible as pending in the same generated ledger.
- 2026-08-26: Count logical problem sets independently from raw URL/file representations. Byte-level
  and semantic mirrors retain provenance but never inflate the logical-set statistic.
- 2026-08-26: The expanded workbook contains 148 concrete P0/P0X candidates after scoped discovery.
  Select 65 for this pass and retain 83 older Grade-9 README scan candidates as `selected=no` so
  their existence is documented without turning the first batch into an unbounded historical run.
- 2026-08-26: For GitHub archives whose repository tree contains only a README, treat images embedded
  under explicit academic-year headings as raw question-page candidates. Preserve every page URL,
  but derive one logical set from the collection/year rather than counting each page as a set.
- 2026-08-26: Official JBMO sources take precedence over mirrors. Mirror HTML snapshots remain
  research references when ordinary access exposes no downloadable question/solution document;
  snapshots do not count as logical problem sets.

- 2026-08-26: Use `chore/bootstrap-chuyen-toan-corpus` because the repository-approved branch
  vocabulary does not include a `data/` prefix; the task is neither application feature nor product
  content publication.
- 2026-08-26: Keep research corpus data outside production `content/` so it cannot be mistaken for
  validated/published content.
- 2026-08-26: Avoid a new spreadsheet dependency by parsing only the required XLSX cell/string/link
  structures with the Python standard library.
- 2026-08-26: After the project owner authorized processing without resolving rights, acquire the
  bounded corpus for research while retaining `rights_status=unknown` and keeping redistribution and
  production use unapproved.
- 2026-08-26: Use a manifest-only Git strategy for this pass. The 140,728,502-byte raw cache and its
  derived files are local and ignored because LFS/object-storage policy is not configured.
- 2026-08-26: Treat a first-party file being located separately from successful acquisition. HNUE
  2023 and the PTNK 2025 answer have official-source evidence but failed direct Drive acquisition.
- 2026-08-26: Leave KHTN round metadata unknown, especially for the multi-cohort 2021 cycle; do not
  apply a family-wide round inference.

## Discoveries

- The workbook's claimed archive depth is high, but most historical file provenance points first to
  community GitHub repositories rather than official per-year publications.
- The workbook includes news sources for HCMC demand/current structure and a government PDF for Ha
  Noi, but no official HCMC historical-paper archive URL.
- Official-source availability in the workbook is strongest for current PTNK material; the other
  families need primary-source discovery before any completeness claim.
- The workbook contains 24 distinct URLs. Enriched primary-source research produces 31 source rows:
  12 authoritative, 5 strong archives, 2 secondary/reporting, and 12 commercial/reference-only.
- The bounded 2017-2026 acquisition plan has 98 candidates. The local cache contains 95 usable
  artifacts and 3 explicit invalid HTML responses from otherwise official Drive candidates.
- PTNK is the only family with usable official files in this pass: 7 files across 2022-2026.
  HNUE 2023 is officially located but its two Drive assets were not downloadable without changing
  access behavior.
- Of 11 PDFs, 5 expose native text, but only 4 pass the conservative research-usefulness heuristic;
  1 text layer is garbled and 6 PDFs are scanned/non-extractable. The archive also contains 84
  images.
- Visual inspection shows a PTNK duration change from 120 minutes in 2022-2023 to 150 minutes in
  2024-2026. Each reviewed paper totals 10 points. HCMC 2025 is also 150 minutes/10 points.
- The expanded workbook has seven sheets, 65 master-queue collections, 155 URL-role occurrences,
  and 99 distinct normalized master-queue URLs. The 65 collections divide into 21 Vietnam, 20
  junior/JBMO, and 24 global rows; 19 are P0/P0X initial-wave rows.
- Scoped discovery produced 148 candidate rows: 65 selected and 83 older Vietnamese Grade-9 scan
  pages deliberately deferred. All 65 selected candidates acquired successfully as 62 unique raw
  objects; three URL/provenance rows reused byte-identical canonical files.
- The expanded batch contains 10 PDFs, 52 PNG scans, and 3 HTML reference snapshots. All PDFs and
  HTML snapshots yielded 13 native-text research artifacts; PNG pages were not OCRed. PDF validation
  recorded 212 aggregate pages and no malformed, checksum, MIME, size, path, or zero-byte errors.
- The new artifacts represent 34 logical sets: Lam Sơn 2017, Hà Nội Grade-9 HSG 2011-2024, TP.HCM
  Grade-9 HSG 2011-2024, national Grade-9 HSG 1995, official JBMO 2022/2024, and two JBMO shortlist
  sets. Multi-year bundles and HTML snapshots remain unsplit references and do not inflate this
  count.
- The official JBMO 2025 host failed DNS lookup, its mirror exposed no downloadable target file,
  and only a reference HTML snapshot was retained. AoPS returned HTTP 403 during J06 discovery;
  no bypass was attempted. J09 and J20 remain index/discovery work rather than downloaded sets.
- Reconciliation resolves 167 provenance rows into 140 set records and 262 components. Of these,
  105 are eligible actual sets and 36 have a source-linked solution; 68 alternate representations
  are preserved without increasing the set count.
- The original five-family scope contains 40 downloaded sets and six source-linked solutions. Nine
  expected actual papers remain missing: TP.HCM 2026; Hà Nội 2018/2025/2026; KHTN
  2017/2018/2026; and HNUE 2025/2026. TP.HCM 2021 is not counted as missing because official-network
  evidence records admission by records rather than this exam.
- The JBMO 2012-2025 bundle contains 14 annual question-and-solution segments. Standalone 2022 and
  2024 files add provenance, not sets; the newly acquired official 2026 question creates one set.
- The owner-provided 181-page Lam Sơn compilation contains 50 numbered source segments: 21
  publisher-claimed actual Chuyên Toán sets (16 with solutions) and 29 adjacent/mock/survey sets.
  Its recent-decade Chuyên Toán scope lacks 2022 and 2023.
- The bounded first-party search found no directly downloadable actual specialist paper for the
  nine missing core cycles. It established cycle/identity evidence and confirmed that HNUE 2025
  official publications expose only a sample paper, which cannot be promoted as the administered
  examination.
- Workbook-authorized TOANMATH and OnThi123 mirrors recover eight missing cycles through seven raw
  objects: TP.HCM 2026; Hà Nội 2018/2025/2026; KHTN 2017/2018/2026; and HNUE 2026. HNUE 2025 is the
  only remaining expected core question gap.
- The recovery batch is four PDFs and three PNGs totaling 38,150,637 bytes. Three PDFs have useful
  native text; the TP.HCM PDF is scanned. All seven pass signature/MIME, size, checksum, path, and
  format validation.
- Visual PDF/image review confirms the mapped question boundaries: TP.HCM pages 1-2, Hà Nội 2018
  page 7, KHTN 2017 page 20, KHTN 2018 page 22, HNUE 2026 pages 24-25, and the three complete PNG
  papers. These are identity/page checks, not expert mathematical review.
- JBMO 2013 and 2020 annual identities are now source-verified against first-party host
  publications. The prior inferred identity labels are removed without changing set or solution
  counts.

## Verification evidence

- `git fetch origin --prune` completed; `origin/main` resolved to
  `88b77350948c5d190208457bf8c8bac5ca5952ee`.
- All 281 lines of `AGENTS.md`, 157 lines of `PLANS.md`, 1,538 lines of
  `docs/MVP_IMPLEMENTATION_PLAN.md`, 14 lines of `CODEX.md`, and 577 lines of the product memo were
  read before implementation.
- A standard-library XLSX inspection enumerated all six visible sheets and every non-empty cell,
  including formulas and URLs.
- `git lfs track` showed no configured patterns; `.gitattributes` is absent.
- `pdfinfo`, `pdftotext`, `pdftoppm`, `file`, `curl`, Python 3.12, and uv are available; `openpyxl` is
  absent.
- All 24 normalized workbook URLs are present in the enriched source inventory; source, file, and
  exam IDs are individually unique.
- `python3 -m scripts.corpus.validate_raw` validated 98 file rows with 84 ambiguity findings and zero
  unexpected validation errors.
- `python3 -m scripts.corpus.validate_manifests` found zero cross-manifest errors.
- Two complete local processing reruns produced byte-identical manifests, reports, and annotation
  artifacts.
- `PYTHONPATH=. uv run --project services/api pytest -q tests/corpus` passed: 17 tests.
- `make format-check`, `make lint`, and `make typecheck` passed after corpus formatting fixes.
- The first root typecheck attempt exposed a stale ignored `.next/types` cache from a completed branch
  switch. Only that generated cache was removed; the immediate rerun and post-rebase rerun passed.
- `uv run --project services/api mypy --config-file services/api/pyproject.toml scripts/corpus`
  passed with no issues in 12 source files.
- `make test-unit` passed: 15 frontend tests and 14 selected API tests; 7 integration tests were
  deselected by the root unit-test contract.
- All ten operator commands returned exit 0 for `--help`. The acquisition command intentionally
  returns exit 1 on the current cache because 3 selected Drive responses remain invalid HTML; it
  still records all 98 outcomes.
- Representative one-page papers for PTNK 2022-2026 and HCMC Sở 2025 were rendered with Poppler and
  visually inspected. Temporary page renders were deleted afterward.
- The complete committed diff was reviewed with `git diff --check`, file/status inspection, and
  object-size inspection. No raw, normalized, extracted, secret, application, database, or product
  content file is committed.
- `git fetch origin --prune` left `origin/main` at
  `88b77350948c5d190208457bf8c8bac5ca5952ee`; `git rebase origin/main` reported the branch up to date.
  Raw validation, extraction, manifest construction, report generation, format, lint, type checks,
  corpus tests, and repository unit tests all passed again after the rebase gate.
- The expanded standard-library workbook import wrote 65 collection rows and 155 URL provenance
  rows. Scoped P0/P0X discovery wrote 148 candidates and three source findings.
- `python3 -m scripts.corpus.download_registry_sources` processed 65 selected candidates: 65
  downloaded, 3 byte-reused, and 0 failed/invalid. Its second run reported 65 unchanged and 0
  network downloads.
- `python3 -m scripts.corpus.validate_registry` validated 65 registry rows with three informational
  duplicate findings and zero errors. `extract_registry_content` produced 13 native-text artifacts
  and 65 normalized sidecars with zero extraction errors.
- A complete expanded build/discover/download/validate/extract/report rerun produced byte-identical
  SHA-256 output for every `registry_*.csv` manifest and `corpus_acquisition_status.md`.
- `PYTHONPATH=. uv run --project services/api pytest -q tests/corpus` passed: 36 tests.
- `uv run --project services/api mypy --config-file services/api/pyproject.toml scripts/corpus`
  passed with no issues in 19 source files.
- `make format-check`, `make lint`, `make typecheck`, and `make test-unit` passed. Unit results were
  15 frontend tests and 14 API tests passed, with 7 API integration tests deselected by contract.
- All six expanded operator commands returned exit 0 for `--help`. The original raw validator also
  passed after being taught to leave `raw/registry/` to the registry validator.
- JBMO 2024 and JBMO 2022 official question PDFs were rendered with Poppler and visually inspected:
  both were readable English contest papers with four problems. Temporary PNG renders were removed.
- `git fetch origin --prune` advanced `origin/main` to
  `984da70f7fb0e51446054f7dea3c852fca08dac0`. `git rebase origin/main` replayed all ten corpus
  commits successfully without conflicts, and `git merge-base --is-ancestor origin/main HEAD`
  returned success.
- Post-rebase corpus verification passed unchanged: legacy validation reported 98 rows, 84 expected
  ambiguity findings, and 0 errors; expanded validation reported 65 rows, 3 duplicate-byte findings,
  and 0 errors; both extraction commands returned 0 errors; cross-manifest validation returned 0
  errors; and all reports regenerated without a Git diff.
- Post-rebase `PYTHONPATH=. uv run --project services/api pytest -q tests/corpus` passed 36 tests,
  and corpus mypy passed all 19 source files.
- Post-rebase `make format-check`, `make lint`, `make typecheck`, and `make test-unit` passed. The
  rebased Milestone 2 tree ran 24 frontend unit tests and 25 API unit tests successfully; 19 API
  integration tests were deselected by the root unit-test contract.
- Final worktree review found only the owner's untracked `docs/research/` inputs and unrelated
  `data/test_problem.jpeg`; neither is staged or modified by this change. Raw, normalized, and
  extracted corpus caches remain ignored.
- The bounded authoritative-source recovery examined 16 targets. Three official/organizer JBMO
  PDFs were verified, fully downloaded, checksummed, validated, and extracted; three official Drive
  candidates remain blocked, five targets have landing-page evidence only, four located publications
  were not the actual specialist paper, and one official JBMO solution was not located.
- `python3 -m scripts.corpus.download_registry_sources` processed 69 selected candidates after
  recovery: 66 cached rows were unchanged and three PDFs downloaded with zero failures. The
  post-rebase rerun reported all 69 unchanged and made zero network downloads.
- `python3 -m scripts.corpus.validate_raw` validated 98 core rows with three expected blocked-HTML
  warnings and zero unexpected errors. `validate_registry` validated 69 rows with three
  duplicate-byte findings and zero errors; registry extraction produced 17 native-text artifacts
  with zero errors.
- `python3 -m scripts.corpus.reconcile_sets` deterministically wrote 140 set records and 262
  components: 105 eligible actual sets and 36 with source-linked solutions. The generated concise
  table reports the original five-family scope as 40 downloaded sets, six with solutions, and nine
  missing expected papers.
- A full second run left every manifest/report SHA-256 unchanged. It performed zero downloads and
  reproduced the same 105/36 set/solution totals.
- Post-rebase `PYTHONPATH=. uv run --project services/api pytest -q tests/corpus` passed 45 tests.
  Corpus mypy passed all 23 source files; `make format-check`, `make lint`, and `make typecheck`
  passed. `make test-unit` passed 63 frontend and 25 API tests, with 19 API integration tests
  deselected by contract. `make content-validate` validated one versioned package.
- The first post-rebase `make typecheck` found a stale local dependency cache after `origin/main`
  added KaTeX/MathLive. `npm ci` synchronized the already-committed lockfile with zero tracked
  changes and zero reported vulnerabilities; the immediate typecheck rerun passed.
- `git fetch origin --prune` advanced `origin/main` to
  `f899a11614784d21b365ad31ff271b7be7e0385c`. The required rebase replayed all 14 corpus commits
  cleanly, and `git merge-base --is-ancestor origin/main HEAD` returned success.
- `python3 -m scripts.corpus.download_sources --exam-variant-prefix question_recovery_` acquired
  seven bounded candidates with zero failures. The immediate rerun reported seven unchanged, zero
  network downloads, and zero failures.
- `python3 -m scripts.corpus.validate_raw` validated 105 core file rows with three pre-existing
  blocked-HTML warnings and zero unexpected errors. Extraction produced eight total core native-text
  artifacts with zero errors; final validation restored the quality-gate status on all usable rows.
- `python3 -m scripts.corpus.reconcile_sets` wrote 148 set records and 270 components: 113 eligible
  actual sets, 36 with source-linked solutions, 48 core question sets, and six core sets with
  solutions. The new recovery file IDs appear in zero exam answer references and zero solution
  components.
- A complete prepare/download/validate/extract/validate/build/report rerun made zero network
  downloads and produced byte-identical manifests, annotations, and reports; aggregate SHA-256 was
  identical before and after.
- All seven recovered PDF page ranges and all three standalone PNG papers were rendered/viewed at
  original detail. The question text is legible and complete within the recorded ranges; temporary
  renders were removed.
- `PYTHONPATH=. uv run --project services/api pytest -q tests/corpus` passed 50 tests. Corpus mypy
  passed all 24 source files; `make format-check`, `make lint`, and `make typecheck` passed.
- `make test-unit` passed 63 frontend and 25 API tests, with 19 API integration tests deselected by
  contract. `make content-validate` validated the one existing versioned package.
- Final `git fetch origin --prune` left `origin/main` at
  `f899a11614784d21b365ad31ff271b7be7e0385c`; `git rebase origin/main` reported the branch up to
  date, and the merge-base ancestor check passed.
- The complete post-rebase rerun again made zero network downloads and produced the byte-identical
  aggregate manifest/report hash
  `55b58a99ae28d150fb13869525817ee62939ec8ffef39307bfd4ff1c5c418873` before and after. Raw
  validation, extraction, final validation, manifest construction, reconciliation, and every report
  completed without errors.
- Post-rebase corpus tests passed 50/50, corpus mypy passed all 24 source files, and
  `make format-check`, `make lint`, and `make typecheck` all passed.
- Before merge, the unpushed branch was reset softly to current `origin/main` and recommitted without
  `data/`. `git ls-files data` returned zero paths, the branch-only commit diff contains no `data/`
  path, and `.gitignore` resolves all local corpus/manual/test files through the `/data/` rule.
- Corpus tests were rerun from an empty temporary working directory with the repository only on
  `PYTHONPATH`; all 46 synthetic/local-fixture tests passed without access to the ignored local
  corpus. Corpus Ruff formatting/check and mypy also passed after the storage-policy rewrite.

## Result

The research corpus and set-level reconciliation are implemented and verified locally. The original
five-family scope contains 48 distinct downloaded sets; alternate files no longer inflate this count.
The expanded scope adds 65 eligible sets: 15 JBMO annual contests, 21 publisher-claimed Lam Sơn
Chuyên Toán papers, 28 recent Grade-9 HSG papers, and one historical national HSG paper. Across both
passes, 174 provenance rows resolve to 148 total set records and 270 components; 113 sets are eligible
actual papers and 36 have a source-linked solution. The only remaining original-plan question gap is
HNUE 2025. Core solution coverage remains six sets because solution seeking was deferred.

The full `data/` tree, including the 233.67 MiB raw cache, manifests, reports, annotations, and
derived artifacts, remains local and ignored. Git contains only reproducible tooling, local-fixture
tests, the root ignore rule, and this ChangePlan. The unpushed branch history is rewritten so no data
path is reachable from the commits that will be merged and pushed. The global P1 wave and the
separate solution-acquisition wave were not started.
