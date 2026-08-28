import hashlib
from pathlib import Path

PROMPT_VERSION = "m7-evaluation-v1"
PROVIDER_SCHEMA_VERSION = "m7-provider-evaluation-v1"
RESULT_SCHEMA_VERSION = "1.0.0"

_PROMPT_PATH = Path(__file__).with_name("prompts") / f"{PROMPT_VERSION}.txt"
PROMPT_TEXT = _PROMPT_PATH.read_text(encoding="utf-8")
PROMPT_HASH = hashlib.sha256(PROMPT_TEXT.encode()).hexdigest()


def provider_instruction(context_json: str, *, repair_schema: bool) -> str:
    instruction = f"{PROMPT_TEXT}\n\nEvaluation context JSON:\n{context_json}"
    if repair_schema:
        instruction += (
            "\n\nThe previous response failed the supplied JSON schema. Return only one corrected "
            "JSON value matching that exact schema. Do not invent or alter learner work."
        )
    return instruction
