from pydantic import TypeAdapter

from app.evaluation.schemas import ProviderEvaluationPayload

PROVIDER_JSON_SCHEMA = TypeAdapter(ProviderEvaluationPayload).json_schema(by_alias=True)

GEMINI_PROVIDER_JSON_SCHEMA: dict[str, object] = {
    "type": "object",
    "properties": {
        "outcome": {"type": "string", "enum": ["ready", "uncertain"]},
        "reasoningSteps": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "stepKey": {"type": "string"},
                    "transcriptBlockIds": {"type": "array", "items": {"type": "string"}},
                    "summary": {"type": "string"},
                    "judgment": {
                        "type": "string",
                        "enum": ["correct", "incorrect", "uncertain", "not_assessable"],
                    },
                    "errorKind": {
                        "type": "string",
                        "enum": ["none", "root", "dependent"],
                    },
                    "dependsOnStepKeys": {"type": "array", "items": {"type": "string"}},
                    "feedback": {"type": "string"},
                },
                "required": [
                    "stepKey",
                    "transcriptBlockIds",
                    "summary",
                    "judgment",
                    "errorKind",
                    "dependsOnStepKeys",
                    "feedback",
                ],
            },
        },
        "rubricAwards": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "rubricCode": {"type": "string"},
                    "awardedScore": {"type": "number"},
                    "explanation": {"type": "string"},
                },
                "required": ["rubricCode", "awardedScore", "explanation"],
            },
        },
        "overallFeedback": {"type": "string"},
        "nextAction": {"type": "string"},
        "reason": {"type": "string"},
        "recommendedAction": {"type": "string", "enum": ["manual_review"]},
    },
    "required": ["outcome"],
}
