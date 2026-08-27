from __future__ import annotations

from collections.abc import Iterable, Mapping
from pathlib import Path

from scripts.corpus.core import deterministic_id

PROBLEM_SET_FIELDS = (
    "set_id",
    "collection_ids",
    "series_id",
    "exam_family",
    "school_or_authority",
    "country_region",
    "calendar_year",
    "academic_year",
    "set_variant",
    "set_kind",
    "subject",
    "specialized_or_common",
    "round",
    "identity_status",
    "completeness_status",
    "corpus_eligibility",
    "question_available",
    "solution_available",
    "official_question_available",
    "official_solution_available",
    "solution_source",
    "primary_question_component_id",
    "primary_solution_component_id",
    "expert_review_status",
    "notes",
)

SET_COMPONENT_FIELDS = (
    "component_id",
    "set_id",
    "file_manifest",
    "file_id",
    "component_role",
    "representation_role",
    "page_start",
    "page_end",
    "sequence",
    "source_type",
    "official_status",
    "classification_provenance",
    "verified",
    "semantic_duplicate_of_component_id",
    "notes",
)

MANUAL_IMPORT_FIELDS = (
    "manual_import_id",
    "collection_id",
    "original_local_path",
    "original_filename",
    "embedded_source_url",
    "exact_source_url",
    "provenance_status",
    "imported_file_id",
    "canonical_raw_path",
    "sha256",
    "file_size",
    "imported_at",
    "notes",
)

CORE_PRIMARY_QUESTIONS = {
    ("ptnk", "2017"): "cand_8d98b20e0512dc47167e",
    ("ptnk", "2018"): "cand_4e6b1c3422b322b75a25",
    ("ptnk", "2019"): "cand_2479d524b99ccc0ef080",
    ("ptnk", "2020"): "cand_c0ad27ff5117d41ebd97",
    ("ptnk", "2021"): "cand_8cb432e5c3c4d8c85f0b",
    ("ptnk", "2022"): "cand_b96101db6487677f394f",
    ("ptnk", "2023"): "cand_7e734bead9dc234046ad",
    ("ptnk", "2024"): "cand_757a8d98fa4029974180",
    ("ptnk", "2025"): "cand_fa512bb6e5612602f586",
    ("ptnk", "2026"): "cand_c47124f49356cdca66e6",
    ("hcmc_so", "2017"): "cand_02a2b522dea72dcdffbf",
    ("hcmc_so", "2018"): "cand_1f1ea9d7a241ef544f1e",
    ("hcmc_so", "2019"): "cand_758879aec5415daa60f8",
    ("hcmc_so", "2020"): "cand_be7c9f8d5393965e9e46",
    ("hcmc_so", "2022"): "cand_f67392582e5c4b4243e6",
    ("hcmc_so", "2023"): "cand_1d6be277d9d9b5cbd6c4",
    ("hcmc_so", "2024"): "cand_a36c59163e63988168a5",
    ("hcmc_so", "2025"): "cand_bc6e96ef45dc19b57c36",
    ("hanoi_so", "2017"): "cand_0dc756b329f2a267ce12",
    ("hanoi_so", "2019"): "cand_aff8475a50c4185ea45f",
    ("hanoi_so", "2020"): "cand_9c34dcbc3aaf63be4ab4",
    ("hanoi_so", "2021"): "cand_641f624f81211a803d28",
    ("hanoi_so", "2022"): "cand_5a62f65599872bfd8592",
    ("hanoi_so", "2023"): "cand_9cc0a7f04c18358af8e0",
    ("hanoi_so", "2024"): "cand_fec9db1daaf53815ac23",
    ("khtn", "2019"): "cand_763baa1a5338231c6a8d",
    ("khtn", "2020"): "cand_1603128bedd655ddfcb3",
    ("khtn", "2021"): "cand_c2b17512a2584136d43a",
    ("khtn", "2022"): "cand_7becc9485adc8c4e0686",
    ("khtn", "2023"): "cand_f4271f8d360a1810d64c",
    ("khtn", "2024"): "cand_c9886a1346bead91bf66",
    ("khtn", "2025"): "cand_8186662d5464ac9c7c9e",
    ("hnue", "2017"): "cand_a34c7fefac73fcb9966b",
    ("hnue", "2018"): "cand_5641223f30313c5f3e65",
    ("hnue", "2019"): "cand_93de6de3d9fd87ab0c52",
    ("hnue", "2020"): "cand_7fb8efe8ceb79662c5bd",
    ("hnue", "2021"): "cand_6ce2bde4100906b98269",
    ("hnue", "2022"): "cand_1217e99bd5572b5f9111",
    ("hnue", "2023"): "cand_761ed6479d73dba3cf16",
    ("hnue", "2024"): "cand_21255560cc2899fb13a6",
}

CORE_SOLUTION_FILES = {
    "cand_5fcbf1391c61c2755d58",
    "cand_278bd9f707f05bd3bd4b",
    "cand_0dc81cff36fe8dd8c88a",
    "cand_b61a663956b5739173ad",
}

CORE_ADJACENT_QUESTIONS = {
    "cand_d2d2369aa33ce934f53a": "specialized_informatics",
    "cand_9347385faa89af5a7c78": "specialized_informatics",
    "cand_b422c64f6d7a0d2ca0ab": "specialized_informatics",
    "cand_773d4105b433f32f20e1": "specialized_informatics",
    "cand_7c605c48025d9a9c5866": "specialized_informatics",
}

CORE_BLOCKED_HTML = {
    "cand_cfa055c2dd716da37381",
    "cand_6c1395018c441f0f2d8f",
    "cand_dde2a0ad21e186a7f3ab",
}

JBMO_RANGES = (
    (2012, 1, 5, "source_explicit"),
    (2013, 6, 10, "source_verified"),
    (2014, 11, 17, "source_explicit"),
    (2015, 18, 21, "source_explicit"),
    (2016, 22, 27, "source_explicit"),
    (2017, 28, 31, "source_explicit"),
    (2018, 32, 35, "source_explicit"),
    (2019, 36, 41, "source_supported"),
    (2020, 42, 46, "source_verified"),
    (2021, 47, 51, "source_explicit"),
    (2022, 52, 59, "source_explicit"),
    (2023, 60, 64, "source_explicit"),
    (2024, 65, 72, "source_supported"),
    (2025, 73, 78, "source_explicit"),
)

# Number, year, track, kind, question start/end, solution start/end.
LAM_SON_SETS = (
    (1, 2026, "specialized_mathematics", "actual_exam", 5, 5, 42, 49),
    (2, 2025, "specialized_mathematics", "actual_exam", 6, 6, 50, 53),
    (3, 2024, "specialized_mathematics", "actual_exam", 7, 7, 54, 57),
    (4, 2024, "specialized_mathematics", "actual_exam", 8, 8, 58, 63),
    (5, 2024, "specialized_mathematics", "actual_exam", 9, 9, 64, 68),
    (6, 2024, "specialized_mathematics", "mock", 10, 10, 69, 72),
    (7, 2022, "specialized_informatics", "actual_exam", 11, 11, 73, 77),
    (8, 2021, "specialized_mathematics", "actual_exam", 11, 12, 78, 81),
    (9, 2020, "specialized_mathematics", "actual_exam", 13, 13, 82, 85),
    (10, 2019, "specialized_informatics", "actual_exam", 13, 13, 86, 89),
    (11, 2019, "specialized_mathematics", "actual_exam", 14, 14, 90, 92),
    (12, 2018, "specialized_mathematics", "actual_exam", 15, 15, 93, 97),
    (13, 2018, "specialized_informatics", "actual_exam", 16, 16, 98, 100),
    (14, 2017, "common_specialized", "actual_exam", 17, 17, 101, 103),
    (15, 2017, "specialized_mathematics", "actual_exam", 18, 18, 104, 106),
    (16, 2016, "common_specialized", "actual_exam", 19, 19, 107, 110),
    (17, 2016, "specialized_mathematics", "actual_exam", 19, 19, 111, 113),
    (18, 2015, "common_specialized", "actual_exam", 20, 20, 114, 117),
    (19, 2015, "specialized_informatics", "actual_exam", 21, 21, 118, 120),
    (20, 2015, "specialized_mathematics", "actual_exam", 22, 22, 121, 121),
    (21, 2014, "specialized_informatics", "actual_exam", 22, 22, 122, 124),
    (22, 2014, "specialized_mathematics", "actual_exam", 23, 23, 125, 127),
    (23, 2014, "common_specialized", "actual_exam", 24, 24, 128, 131),
    (24, 2013, "russian_french", "actual_exam", 25, 25, 132, 133),
    (25, 2013, "specialized_mathematics", "actual_exam", 25, 25, None, None),
    (26, 2013, "specialized_informatics", "actual_exam", 26, 26, 134, 135),
    (27, 2012, "common_specialized", "actual_exam", 27, 27, 136, 137),
    (28, 2012, "specialized_informatics", "actual_exam", 28, 28, 138, 141),
    (29, 2012, "common_specialized", "actual_exam", 28, 28, 142, 143),
    (30, 2012, "russian_french", "actual_exam", 29, 29, 144, 147),
    (31, 2012, "specialized_mathematics", "actual_exam", 30, 30, 148, 150),
    (32, 2011, "specialized_informatics", "actual_exam", 31, 31, 151, 152),
    (33, 2011, "common_specialized", "actual_exam", 31, 31, 153, 155),
    (34, 2010, "specialized_mathematics", "actual_exam", 32, 32, 156, 160),
    (35, 2010, "common_specialized", "actual_exam", 33, 33, 161, 162),
    (36, 2009, "specialized_mathematics", "actual_exam", 34, 34, 163, 165),
    (37, 2009, "specialized_informatics", "actual_exam", 34, 34, None, None),
    (38, 2008, "specialized_informatics", "actual_exam", 35, 35, None, None),
    (39, 2008, "specialized_mathematics", "actual_exam", 36, 36, None, None),
    (40, 2007, "specialized_mathematics", "actual_exam", 37, 37, None, None),
    (41, 2006, "specialized_mathematics", "actual_exam", 37, 37, None, None),
    (42, 2005, "specialized_informatics", "actual_exam", 38, 38, None, None),
    (43, 2005, "russian_french", "actual_exam", 39, 39, None, None),
    (44, 2004, "common_specialized", "actual_exam", 39, 39, None, None),
    (45, 2004, "specialized_informatics", "actual_exam", 40, 40, None, None),
    (46, 2003, "russian_french", "actual_exam", 41, 41, None, None),
    (47, 2003, "specialized_mathematics", "actual_exam", 41, 42, None, None),
    (48, 2024, "specialized_mathematics", "survey", 166, 166, 167, 171),
    (49, 2024, "specialized_informatics", "survey", 172, 172, 173, 175),
    (50, 2025, "specialized_mathematics", "survey", 176, 177, 177, 181),
)

LAM_SON_MANUAL_PATH = Path(
    "data/manual_downloaded/Tuyen tap de thi vao lop 10 chuyen Lam Son - Thanh Hoa.pdf"
)
LAM_SON_SOURCE_URL = "https://tailieumontoan.com/"
JBMO_BUNDLE_FILE_ID = "gcand_c8718c50f1476fbe514d"


def canonical_set_id(series_id: str, year: str | int, variant: str) -> str:
    return deterministic_id("pset", series_id, str(year), variant)


def component_id(
    set_id: str,
    file_id: str,
    role: str,
    page_start: str | int | None = None,
    page_end: str | int | None = None,
) -> str:
    return deterministic_id(
        "component",
        set_id,
        file_id,
        role,
        str(page_start or ""),
        str(page_end or ""),
    )


def merge_set_rows(rows: Iterable[Mapping[str, object]]) -> list[dict[str, object]]:
    merged: dict[str, dict[str, object]] = {}
    for source in rows:
        row = dict(source)
        set_id = str(row["set_id"])
        existing = merged.get(set_id)
        if existing is None:
            merged[set_id] = row
            continue
        collections = set(filter(None, str(existing["collection_ids"]).split(";")))
        collections.update(filter(None, str(row["collection_ids"]).split(";")))
        existing["collection_ids"] = ";".join(sorted(collections))
        existing["notes"] = " ".join(
            dict.fromkeys(filter(None, (str(existing["notes"]), str(row["notes"]))))
        )
    return [merged[key] for key in sorted(merged)]
