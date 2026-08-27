import hashlib
import json
from pathlib import Path

FIXTURE_ROOT = Path(__file__).resolve().parents[1] / "fixtures" / "transcription"


def test_transcription_fixture_manifest_is_complete_synthetic_and_content_addressed() -> None:
    manifest = json.loads((FIXTURE_ROOT / "manifest.json").read_text(encoding="utf-8"))

    assert manifest["schemaVersion"] == "1.0.0"
    assert manifest["provenance"] == {
        "classification": "original_synthetic_non_personal",
        "createdAt": "2026-08-28",
        "creator": "Math Coach application team",
        "generator": "Committed SVG source rendered with FFmpeg 6.1.1-3ubuntu5 and librsvg",
        "personalData": False,
        "providerResponse": False,
        "realExaminationContent": False,
        "realLearnerWork": False,
    }
    fixtures = manifest["fixtures"]
    assert len(fixtures) == 11
    assert {fixture["category"] for fixture in fixtures} >= {
        "clean_handwritten_mathematics",
        "messy_but_readable_mathematics",
        "mixed_vietnamese_text_and_mathematics",
        "cross_outs_and_insertions",
        "correct_standard_solution",
        "correct_alternative_solution",
        "subtle_mathematical_error",
        "incomplete_solution",
        "geometry_solution",
        "alternating_text_and_math_on_one_line",
        "warnings_and_optional_source_regions",
    }
    for fixture in fixtures:
        image = FIXTURE_ROOT / fixture["imagePath"]
        source = FIXTURE_ROOT / fixture["sourcePath"]
        assert image.is_file()
        assert source.is_file()
        assert hashlib.sha256(image.read_bytes()).hexdigest() == fixture["sha256"]
        assert fixture["expectedBlocks"]
        assert all(block["type"] in {"text", "math"} for block in fixture["expectedBlocks"])

    subtle = next(fixture for fixture in fixtures if fixture["name"] == "subtle-error-preserved")
    assert subtle["mathematicalErrorMustRemain"] is True
    assert any(block.get("latex") == "(a+b)^2=a^2+b^2" for block in subtle["expectedBlocks"])
