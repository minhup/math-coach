import hashlib
from pathlib import Path

PROMPT_VERSION = "m6-faithful-transcription-v1"
PROVIDER_SCHEMA_VERSION = "m6-provider-transcript-v1"
TRANSCRIPT_SCHEMA_VERSION = "3.0.0"

_PROMPT_PATH = Path(__file__).with_name("prompts") / f"{PROMPT_VERSION}.txt"
PROMPT_TEXT = _PROMPT_PATH.read_text(encoding="utf-8")
PROMPT_HASH = hashlib.sha256(PROMPT_TEXT.encode()).hexdigest()


def provider_instruction(problem_context: str, *, repair_schema: bool) -> str:
    instruction = f"{PROMPT_TEXT}\n\nProblem context:\n{problem_context}"
    if repair_schema:
        instruction += (
            "\n\nThe previous response failed the supplied JSON schema. Return only one corrected "
            "JSON value matching that exact schema. Do not change or correct the learner's work."
        )
    return instruction
