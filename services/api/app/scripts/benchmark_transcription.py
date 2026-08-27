import argparse
import asyncio
import hashlib
import json
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from time import perf_counter
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter

from app.transcription.provider import (
    ProviderPermanentError,
    ProviderRequest,
    ProviderSchemaError,
    ProviderTransportError,
    StrictTranscriptionProvider,
)
from app.transcription.schemas import TranscriptDocument
from app.transcription.service import get_transcription_provider

MAX_INPUT_TOKENS_PER_CALL = 10_000
MAX_OUTPUT_TOKENS_PER_CALL = 3_000
MAX_SCHEMA_ATTEMPTS = 2
SYNTHETIC_ATTEMPT_ID = uuid.UUID("60000000-0000-4000-8000-000000000200")


class BenchmarkModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class ExpectedTextBlock(BenchmarkModel):
    type: Literal["text"]
    text: str


class ExpectedMathBlock(BenchmarkModel):
    type: Literal["math"]
    latex: str


ExpectedBlock = Annotated[
    ExpectedTextBlock | ExpectedMathBlock,
    Field(discriminator="type"),
]


class SyntheticProvenance(BenchmarkModel):
    classification: Literal["original_synthetic_non_personal"]
    created_at: str = Field(alias="createdAt")
    creator: str
    generator: str
    personal_data: Literal[False] = Field(alias="personalData")
    provider_response: Literal[False] = Field(alias="providerResponse")
    real_examination_content: Literal[False] = Field(alias="realExaminationContent")
    real_learner_work: Literal[False] = Field(alias="realLearnerWork")


class SyntheticFixture(BenchmarkModel):
    name: str
    category: str
    image_path: str = Field(alias="imagePath")
    source_path: str = Field(alias="sourcePath")
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    expected_blocks: list[ExpectedBlock] = Field(alias="expectedBlocks", min_length=1)
    expected_warning_codes: list[str] = Field(
        default_factory=list,
        alias="expectedWarningCodes",
    )
    mathematical_error_must_remain: bool = Field(
        default=False,
        alias="mathematicalErrorMustRemain",
    )
    source_regions_expected: bool = Field(default=False, alias="sourceRegionsExpected")


class SyntheticManifest(BenchmarkModel):
    schema_version: Literal["1.0.0"] = Field(alias="schemaVersion")
    provenance: SyntheticProvenance
    fixtures: list[SyntheticFixture] = Field(min_length=1)


manifest_adapter = TypeAdapter(SyntheticManifest)


def _owned_path(root: Path, relative: str) -> Path:
    resolved_root = root.resolve()
    resolved = (resolved_root / relative).resolve()
    if resolved_root not in resolved.parents:
        raise ValueError("Synthetic fixture path escapes its repository-owned root")
    return resolved


def load_synthetic_manifest(root: Path) -> SyntheticManifest:
    manifest_path = root / "manifest.json"
    manifest = manifest_adapter.validate_json(manifest_path.read_text(encoding="utf-8"))
    for fixture in manifest.fixtures:
        image_path = _owned_path(root, fixture.image_path)
        source_path = _owned_path(root, fixture.source_path)
        if not image_path.is_file() or not source_path.is_file():
            raise ValueError(f"Synthetic fixture files are missing: {fixture.name}")
        if hashlib.sha256(image_path.read_bytes()).hexdigest() != fixture.sha256:
            raise ValueError(f"Synthetic fixture hash changed: {fixture.name}")
    return manifest


def estimated_maximum_cost(
    provider: StrictTranscriptionProvider,
    *,
    fixture_count: int,
) -> Decimal:
    return provider.cost(
        input_tokens=fixture_count * MAX_SCHEMA_ATTEMPTS * MAX_INPUT_TOKENS_PER_CALL,
        output_tokens=fixture_count * MAX_SCHEMA_ATTEMPTS * MAX_OUTPUT_TOKENS_PER_CALL,
    )


def assert_benchmark_approval(
    *,
    provider: StrictTranscriptionProvider,
    approved_provider: str,
    approved_model: str,
    approved_fixture_count: int,
    actual_fixture_count: int,
    approved_max_cost_usd: Decimal,
    acknowledge_synthetic_only: bool,
    acknowledge_paid_network_calls: bool,
) -> None:
    identity = provider.identity
    if identity.provider == "application-owned-deterministic-fake":
        raise ValueError("The paid benchmark requires a configured real provider")
    if not acknowledge_synthetic_only or not acknowledge_paid_network_calls:
        raise ValueError("The synthetic-data and paid-network acknowledgements are required")
    if (identity.provider, identity.model_snapshot) != (approved_provider, approved_model):
        raise ValueError("Configured provider/model differs from the explicit approval")
    if approved_fixture_count != actual_fixture_count:
        raise ValueError("Configured fixture count differs from the explicit approval")
    estimate = estimated_maximum_cost(provider, fixture_count=actual_fixture_count)
    if approved_max_cost_usd < estimate:
        raise ValueError("Approved maximum cost is below the conservative benchmark estimate")


def _expected_blocks(fixture: SyntheticFixture) -> list[dict[str, str]]:
    return [block.model_dump(mode="json") for block in fixture.expected_blocks]


def _validated_blocks(document: TranscriptDocument) -> list[dict[str, str]]:
    return [
        {
            "type": block.type,
            "text" if block.type == "text" else "latex": block.text
            if block.type == "text"
            else block.latex,
        }
        for block in document.blocks
    ]


def _comparison(
    expected: list[dict[str, str]],
    actual: list[dict[str, str]],
) -> tuple[int, int, int]:
    text_edits = 0
    math_edits = 0
    ordering_errors = abs(len(expected) - len(actual))
    for expected_block, actual_block in zip(expected, actual, strict=False):
        if expected_block["type"] != actual_block["type"]:
            ordering_errors += 1
        elif expected_block != actual_block:
            if expected_block["type"] == "text":
                text_edits += 1
            else:
                math_edits += 1
    return text_edits, math_edits, ordering_errors


async def run_benchmark(
    *,
    root: Path,
    manifest: SyntheticManifest,
    provider: StrictTranscriptionProvider,
    approved_max_cost_usd: Decimal,
) -> dict[str, object]:
    identity = provider.identity
    results: list[dict[str, object]] = []
    total_cost = Decimal("0")
    budget_exceeded = False
    for fixture in manifest.fixtures:
        image = _owned_path(root, fixture.image_path).read_bytes()
        asset_id = uuid.uuid5(SYNTHETIC_ATTEMPT_ID, fixture.sha256)
        started = perf_counter()
        try:
            result = await provider.transcribe(
                ProviderRequest(
                    attempt_id=SYNTHETIC_ATTEMPT_ID,
                    attempt_asset_id=asset_id,
                    content_type="image/png",
                    image_bytes=image,
                    problem_context="Repository-owned synthetic mathematics benchmark fixture.",
                )
            )
            total_cost += result.cost_usd
            actual = [] if result.transcript is None else _validated_blocks(result.transcript)
            expected = _expected_blocks(fixture)
            text_edits, math_edits, ordering_errors = _comparison(expected, actual)
            expected_math = {block["latex"] for block in expected if block["type"] == "math"}
            actual_math = {block["latex"] for block in actual if block["type"] == "math"}
            warning_codes = [warning.code for warning in result.warnings]
            source_region_count = (
                0
                if result.transcript is None
                else sum(block.source_region is not None for block in result.transcript.blocks)
            )
            results.append(
                {
                    "fixture": fixture.name,
                    "fixtureSha256": fixture.sha256,
                    "expectedFlatTranscript": expected,
                    "validatedProviderTranscript": None
                    if result.transcript is None
                    else result.transcript.model_dump(
                        by_alias=True,
                        exclude_none=True,
                        mode="json",
                    ),
                    "outcome": result.outcome,
                    "textEditsRequired": text_edits,
                    "visualMathEditsRequired": math_edits,
                    "orderingErrors": ordering_errors,
                    "mathematicalErrorPreserved": None
                    if not fixture.mathematical_error_must_remain
                    else expected_math.issubset(actual_math),
                    "warningCodesExpected": fixture.expected_warning_codes,
                    "warningCodes": warning_codes,
                    "warningCodesMatch": set(fixture.expected_warning_codes) == set(warning_codes),
                    "sourceRegionsExpected": fixture.source_regions_expected,
                    "sourceRegionCount": source_region_count,
                    "sourceRegionsPresent": source_region_count > 0,
                    "schemaAttempts": result.schema_attempts,
                    "latencyMs": result.latency_ms,
                    "inputTokens": result.input_tokens,
                    "outputTokens": result.output_tokens,
                    "costUsd": str(result.cost_usd),
                    "failureCode": None,
                }
            )
        except ProviderSchemaError as error:
            cost = provider.cost(
                input_tokens=error.input_tokens,
                output_tokens=error.output_tokens,
            )
            total_cost += cost
            results.append(
                {
                    "fixture": fixture.name,
                    "fixtureSha256": fixture.sha256,
                    "expectedFlatTranscript": _expected_blocks(fixture),
                    "validatedProviderTranscript": None,
                    "outcome": "failed",
                    "schemaAttempts": error.schema_attempts,
                    "latencyMs": error.latency_ms,
                    "inputTokens": error.input_tokens,
                    "outputTokens": error.output_tokens,
                    "costUsd": str(cost),
                    "failureCode": "invalid_schema",
                }
            )
        except (ProviderTransportError, ProviderPermanentError) as error:
            results.append(
                {
                    "fixture": fixture.name,
                    "fixtureSha256": fixture.sha256,
                    "expectedFlatTranscript": _expected_blocks(fixture),
                    "validatedProviderTranscript": None,
                    "outcome": "failed",
                    "schemaAttempts": 0,
                    "latencyMs": max(0, round((perf_counter() - started) * 1000)),
                    "inputTokens": None,
                    "outputTokens": None,
                    "costUsd": None,
                    "failureCode": error.code,
                }
            )
        if total_cost > approved_max_cost_usd:
            budget_exceeded = True
            break

    return {
        "status": "budget_exceeded" if budget_exceeded else "measured_not_a_release_gate",
        "runDate": datetime.now(UTC).isoformat(),
        "provider": identity.provider,
        "modelSnapshot": identity.model_snapshot,
        "promptVersion": identity.prompt_version,
        "promptHash": identity.prompt_hash,
        "schemaVersion": identity.schema_version,
        "pricingVersion": identity.pricing_version,
        "configuration": {
            "fixtureCount": len(manifest.fixtures),
            "maximumSchemaAttemptsPerFixture": MAX_SCHEMA_ATTEMPTS,
            "maximumOutputTokensPerCall": MAX_OUTPUT_TOKENS_PER_CALL,
            "inputTokenEstimatePerCall": MAX_INPUT_TOKENS_PER_CALL,
            "approvedMaximumCostUsd": str(approved_max_cost_usd),
            "estimatedMaximumCostUsd": str(
                estimated_maximum_cost(provider, fixture_count=len(manifest.fixtures))
            ),
        },
        "results": results,
        "totalCostUsd": str(total_cost),
        "limitations": [
            "Input image tokenization is provider-controlled; the input-token ceiling is an "
            "estimate.",
            "Measured values are evidence only and are not a production approval or release gate.",
            "Only repository-owned synthetic, non-personal fixtures are permitted.",
        ],
    }


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description="Run the opt-in paid synthetic M6 benchmark")
    value.add_argument("--fixture-root", type=Path, default=Path("tests/fixtures/transcription"))
    value.add_argument("--output", type=Path, required=True)
    value.add_argument("--approved-provider", required=True)
    value.add_argument("--approved-model", required=True)
    value.add_argument("--approved-fixture-count", type=int, required=True)
    value.add_argument("--approved-max-cost-usd", type=Decimal, required=True)
    value.add_argument("--acknowledge-synthetic-only", action="store_true")
    value.add_argument("--acknowledge-paid-network-calls", action="store_true")
    return value


def main() -> int:
    args = parser().parse_args()
    manifest = load_synthetic_manifest(args.fixture_root)
    provider = get_transcription_provider()
    assert_benchmark_approval(
        provider=provider,
        approved_provider=args.approved_provider,
        approved_model=args.approved_model,
        approved_fixture_count=args.approved_fixture_count,
        actual_fixture_count=len(manifest.fixtures),
        approved_max_cost_usd=args.approved_max_cost_usd,
        acknowledge_synthetic_only=args.acknowledge_synthetic_only,
        acknowledge_paid_network_calls=args.acknowledge_paid_network_calls,
    )
    report = asyncio.run(
        run_benchmark(
            root=args.fixture_root,
            manifest=manifest,
            provider=provider,
            approved_max_cost_usd=args.approved_max_cost_usd,
        )
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return 3 if report["status"] == "budget_exceeded" else 0


if __name__ == "__main__":
    raise SystemExit(main())
