import type { components } from "@math-coach/api-client";

import { invalidResponse } from "./api";
import { apiRequest } from "./api-transport";
import { isStrictContentBlocks } from "./static-journey-api";

export type ReadyEvaluation = components["schemas"]["ReadyEvaluationResponse"];
export type UncertainEvaluation = components["schemas"]["UncertainEvaluationResponse"];
export type Evaluation = ReadyEvaluation | UncertainEvaluation;
export type EvaluationState =
  | components["schemas"]["EvaluationNotStartedState"]
  | components["schemas"]["EvaluationProcessingState"]
  | components["schemas"]["EvaluationReadyState"]
  | components["schemas"]["EvaluationUncertainState"]
  | components["schemas"]["EvaluationFailureState"];

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function hasOnlyKeys(value: Record<string, unknown>, keys: readonly string[]): boolean {
  return Object.keys(value).every((key) => keys.includes(key));
}

function isNullableNonNegativeInteger(value: unknown): boolean {
  return value === null || (Number.isInteger(value) && Number(value) >= 0);
}

function isNullableString(value: unknown): value is string | null {
  return value === null || typeof value === "string";
}

function isDecimal(value: unknown): value is string {
  return typeof value === "string" && /^\d+(?:\.\d{1,6})?$/.test(value);
}

function cents(value: string): number | null {
  if (!/^\d+(?:\.\d{1,2})?$/.test(value)) {
    return null;
  }
  const [whole, fraction = ""] = value.split(".");
  return Number(whole) * 100 + Number(fraction.padEnd(2, "0"));
}

function isEvaluationRun(value: unknown): value is components["schemas"]["EvaluationRunResponse"] {
  return (
    isObject(value) &&
    hasOnlyKeys(value, [
      "completedAt",
      "costUsd",
      "errorCode",
      "id",
      "inputTokens",
      "latencyMs",
      "modelSnapshot",
      "outputTokens",
      "pricingVersion",
      "promptHash",
      "promptVersion",
      "provider",
      "retryCount",
      "schemaAttempts",
      "schemaVersion",
      "startedAt",
      "status",
    ]) &&
    [
      "id",
      "modelSnapshot",
      "pricingVersion",
      "promptVersion",
      "provider",
      "schemaVersion",
      "startedAt",
    ].every((key) => typeof value[key] === "string") &&
    typeof value.promptHash === "string" &&
    /^[0-9a-f]{64}$/.test(value.promptHash) &&
    isNullableString(value.completedAt) &&
    isNullableString(value.errorCode) &&
    (value.costUsd === null || isDecimal(value.costUsd)) &&
    isNullableNonNegativeInteger(value.inputTokens) &&
    isNullableNonNegativeInteger(value.latencyMs) &&
    isNullableNonNegativeInteger(value.outputTokens) &&
    Number.isInteger(value.retryCount) &&
    Number(value.retryCount) >= 0 &&
    Number(value.retryCount) <= 1 &&
    Number.isInteger(value.schemaAttempts) &&
    Number(value.schemaAttempts) >= 0 &&
    Number(value.schemaAttempts) <= 2 &&
    [
      "processing",
      "succeeded",
      "uncertain",
      "retryable_failure",
      "permanent_failure",
      "invalid_schema",
    ].includes(String(value.status))
  );
}

function isReasoningStep(value: unknown): value is components["schemas"]["ReasoningStepResponse"] {
  return (
    isObject(value) &&
    hasOnlyKeys(value, [
      "dependsOnStepIds",
      "errorKind",
      "feedback",
      "id",
      "judgment",
      "position",
      "summary",
      "transcriptBlockIds",
    ]) &&
    typeof value.id === "string" &&
    Number.isInteger(value.position) &&
    Number(value.position) >= 1 &&
    ["correct", "incorrect", "uncertain", "not_assessable"].includes(String(value.judgment)) &&
    ["none", "root", "dependent"].includes(String(value.errorKind)) &&
    Array.isArray(value.transcriptBlockIds) &&
    value.transcriptBlockIds.length > 0 &&
    value.transcriptBlockIds.every((item) => typeof item === "string") &&
    new Set(value.transcriptBlockIds).size === value.transcriptBlockIds.length &&
    Array.isArray(value.dependsOnStepIds) &&
    value.dependsOnStepIds.every((item) => typeof item === "string") &&
    new Set(value.dependsOnStepIds).size === value.dependsOnStepIds.length &&
    isStrictContentBlocks(value.summary) &&
    value.summary.length > 0 &&
    isStrictContentBlocks(value.feedback) &&
    value.feedback.length > 0
  );
}

function isRubricScore(value: unknown): value is components["schemas"]["RubricScoreResponse"] {
  if (
    !isObject(value) ||
    !hasOnlyKeys(value, [
      "awardedScore",
      "explanation",
      "maximumScore",
      "rubricCode",
      "rubricItemId",
    ]) ||
    typeof value.rubricCode !== "string" ||
    typeof value.rubricItemId !== "string" ||
    !isDecimal(value.awardedScore) ||
    !isDecimal(value.maximumScore) ||
    !isStrictContentBlocks(value.explanation) ||
    value.explanation.length === 0
  ) {
    return false;
  }
  const awarded = cents(value.awardedScore);
  const maximum = cents(value.maximumScore);
  return awarded !== null && maximum !== null && maximum > 0 && awarded <= maximum;
}

function readyRelationshipsAreValid(value: ReadyEvaluation): boolean {
  const positions = new Map(value.reasoningSteps.map((step, index) => [step.id, index]));
  if (
    positions.size !== value.reasoningSteps.length ||
    value.reasoningSteps.some((step, index) => step.position !== index + 1) ||
    new Set(value.rubricBreakdown.map(({ rubricItemId }) => rubricItemId)).size !==
      value.rubricBreakdown.length
  ) {
    return false;
  }
  for (const [index, step] of value.reasoningSteps.entries()) {
    if (step.dependsOnStepIds.some((dependency) => (positions.get(dependency) ?? index) >= index)) {
      return false;
    }
    if (step.judgment === "incorrect" && step.errorKind === "none") {
      return false;
    }
    if (step.judgment !== "incorrect" && step.errorKind !== "none") {
      return false;
    }
    if (step.errorKind === "dependent" && step.dependsOnStepIds.length === 0) {
      return false;
    }
    if (step.errorKind !== "dependent" && step.dependsOnStepIds.length > 0) {
      return false;
    }
  }
  const score = cents(value.score);
  const maximum = cents(value.maximumScore);
  const awarded = value.rubricBreakdown.reduce(
    (total, item) => total + (cents(item.awardedScore) ?? 0),
    0,
  );
  const rubricMaximum = value.rubricBreakdown.reduce(
    (total, item) => total + (cents(item.maximumScore) ?? 0),
    0,
  );
  return score !== null && maximum !== null && score === awarded && maximum === rubricMaximum;
}

export function parseEvaluation(value: unknown): Evaluation {
  if (!isObject(value)) {
    return invalidResponse();
  }
  if (value.outcome === "uncertain") {
    if (
      !hasOnlyKeys(value, [
        "confirmedTranscriptVersionId",
        "evaluationId",
        "outcome",
        "reason",
        "recommendedAction",
        "run",
      ]) ||
      typeof value.confirmedTranscriptVersionId !== "string" ||
      typeof value.evaluationId !== "string" ||
      value.recommendedAction !== "manual_review" ||
      !isStrictContentBlocks(value.reason) ||
      value.reason.length === 0 ||
      !isEvaluationRun(value.run) ||
      value.run.status !== "uncertain"
    ) {
      return invalidResponse();
    }
    return {
      confirmedTranscriptVersionId: value.confirmedTranscriptVersionId,
      evaluationId: value.evaluationId,
      outcome: "uncertain",
      reason: value.reason,
      recommendedAction: "manual_review",
      run: value.run,
    };
  }
  if (
    value.outcome !== "ready" ||
    !hasOnlyKeys(value, [
      "confirmedTranscriptVersionId",
      "evaluationId",
      "feedback",
      "maximumScore",
      "nextSteps",
      "outcome",
      "reasoningSteps",
      "referenceSolutionsNonExhaustive",
      "rubricBreakdown",
      "run",
      "score",
    ]) ||
    typeof value.confirmedTranscriptVersionId !== "string" ||
    typeof value.evaluationId !== "string" ||
    value.referenceSolutionsNonExhaustive !== true ||
    !isDecimal(value.score) ||
    !isDecimal(value.maximumScore) ||
    !Array.isArray(value.reasoningSteps) ||
    value.reasoningSteps.length === 0 ||
    !value.reasoningSteps.every(isReasoningStep) ||
    !Array.isArray(value.rubricBreakdown) ||
    value.rubricBreakdown.length === 0 ||
    !value.rubricBreakdown.every(isRubricScore) ||
    !isStrictContentBlocks(value.feedback) ||
    value.feedback.length === 0 ||
    !isStrictContentBlocks(value.nextSteps) ||
    value.nextSteps.length === 0 ||
    !isEvaluationRun(value.run) ||
    value.run.status !== "succeeded"
  ) {
    return invalidResponse();
  }
  const ready: ReadyEvaluation = {
    confirmedTranscriptVersionId: value.confirmedTranscriptVersionId,
    evaluationId: value.evaluationId,
    feedback: value.feedback,
    maximumScore: value.maximumScore,
    nextSteps: value.nextSteps,
    outcome: "ready",
    reasoningSteps: value.reasoningSteps,
    referenceSolutionsNonExhaustive: true,
    rubricBreakdown: value.rubricBreakdown,
    run: value.run,
    score: value.score,
  };
  return readyRelationshipsAreValid(ready) ? ready : invalidResponse();
}

export function requestEvaluation(
  attemptId: string,
  confirmedTranscriptVersionId: string,
  idempotencyKey: string = crypto.randomUUID(),
): Promise<Evaluation> {
  return apiRequest(`/api/v1/attempts/${attemptId}/evaluation`, parseEvaluation, {
    body: JSON.stringify({ confirmedTranscriptVersionId, idempotencyKey }),
    method: "POST",
  });
}

function parseEvaluationState(value: unknown): EvaluationState {
  if (!isObject(value) || typeof value.state !== "string") {
    return invalidResponse();
  }
  if (value.state === "not_started" && hasOnlyKeys(value, ["state"])) {
    return { state: "not_started" };
  }
  if (
    value.state === "processing" &&
    hasOnlyKeys(value, ["run", "state"]) &&
    isEvaluationRun(value.run) &&
    value.run.status === "processing"
  ) {
    return { run: value.run, state: "processing" };
  }
  if (
    (value.state === "ready" || value.state === "uncertain") &&
    hasOnlyKeys(value, ["result", "state"]) &&
    isObject(value.result)
  ) {
    const result = parseEvaluation(value.result);
    if (result.outcome === "ready" && value.state === "ready") {
      return { result, state: "ready" };
    }
    if (result.outcome === "uncertain" && value.state === "uncertain") {
      return { result, state: "uncertain" };
    }
  }
  if (
    ["retryable_failure", "permanent_failure", "invalid_schema"].includes(value.state) &&
    hasOnlyKeys(value, ["run", "state"]) &&
    isEvaluationRun(value.run) &&
    value.run.status === value.state
  ) {
    if (value.state === "retryable_failure") {
      return { run: value.run, state: "retryable_failure" };
    }
    if (value.state === "permanent_failure") {
      return { run: value.run, state: "permanent_failure" };
    }
    return { run: value.run, state: "invalid_schema" };
  }
  return invalidResponse();
}

export function getEvaluationState(attemptId: string): Promise<EvaluationState> {
  return apiRequest(`/api/v1/attempts/${attemptId}/evaluation`, parseEvaluationState);
}
