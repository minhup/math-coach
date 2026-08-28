import type { components } from "@math-coach/api-client";

import { invalidResponse, isGeometryAction, isGeometryScene } from "./api";
import { apiRequest } from "./api-transport";

export type AvailableExamCycles = components["schemas"]["AvailableExamCycleListResponse"];
export type StaticDailyPlan = components["schemas"]["StaticDailyPlanResponse"];
export type NextHint = components["schemas"]["NextHintResponse"];
export type ConceptVersion = components["schemas"]["ConceptVersionResponse"];
export type StudyProfile = components["schemas"]["StudyProfileResponse"];
export type ExamTarget = components["schemas"]["ExamTargetResponse"];
export type Attempt = components["schemas"]["AttemptResponse"];
type JourneyContentBlock = StaticDailyPlan["items"][number]["problem"]["statement"][number];

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function hasOnlyKeys(value: Record<string, unknown>, keys: readonly string[]): boolean {
  return Object.keys(value).every((key) => keys.includes(key));
}

function hasStrings<Key extends string>(
  value: Record<string, unknown>,
  keys: readonly Key[],
): value is Record<Key, string> & Record<string, unknown> {
  return keys.every((key) => typeof value[key] === "string");
}

function isNullableString(value: unknown): value is string | null {
  return value === null || typeof value === "string";
}

function isExamTarget(value: unknown): value is ExamTarget {
  return (
    isObject(value) &&
    hasOnlyKeys(value, [
      "createdAt",
      "examCode",
      "examCycleId",
      "examDate",
      "examId",
      "examName",
      "id",
      "priorityRank",
      "status",
      "targetScore",
    ]) &&
    hasStrings(value, [
      "createdAt",
      "examCode",
      "examCycleId",
      "examDate",
      "examId",
      "examName",
      "id",
      "targetScore",
    ]) &&
    Number.isInteger(value.priorityRank) &&
    Number(value.priorityRank) >= 1 &&
    (value.status === "active" || value.status === "completed" || value.status === "archived")
  );
}

function isStudyProfile(value: unknown): value is StudyProfile {
  return (
    isObject(value) &&
    hasOnlyKeys(value, [
      "createdAt",
      "id",
      "name",
      "status",
      "studentExamTargets",
      "updatedAt",
      "weeklyStudyMinutes",
    ]) &&
    hasStrings(value, ["createdAt", "id", "name", "updatedAt"]) &&
    (value.status === "active" || value.status === "archived") &&
    Number.isInteger(value.weeklyStudyMinutes) &&
    Number(value.weeklyStudyMinutes) > 0 &&
    Array.isArray(value.studentExamTargets) &&
    value.studentExamTargets.every(isExamTarget)
  );
}

function parseStudyProfile(value: unknown): StudyProfile {
  if (!isStudyProfile(value)) {
    return invalidResponse();
  }
  return value;
}

function parseExamTarget(value: unknown): ExamTarget {
  if (!isExamTarget(value)) {
    return invalidResponse();
  }
  return value;
}

function isAvailableExamCycle(value: unknown): value is AvailableExamCycles["items"][number] {
  return (
    isObject(value) &&
    hasOnlyKeys(value, ["cycleCode", "examCode", "examDate", "examId", "examName", "id", "year"]) &&
    hasStrings(value, ["cycleCode", "examCode", "examDate", "examId", "examName", "id"]) &&
    Number.isInteger(value.year)
  );
}

function parseAvailableExamCycles(value: unknown): AvailableExamCycles {
  if (
    !isObject(value) ||
    !hasOnlyKeys(value, ["items"]) ||
    !Array.isArray(value.items) ||
    !value.items.every(isAvailableExamCycle)
  ) {
    return invalidResponse();
  }
  return { items: value.items };
}

function parseAttempt(value: unknown): Attempt {
  if (
    !isObject(value) ||
    !hasOnlyKeys(value, ["createdAt", "id", "problemVersionId", "status", "studyProfileId"]) ||
    !hasStrings(value, ["createdAt", "id", "problemVersionId", "studyProfileId"]) ||
    (value.status !== "draft" && value.status !== "submitted")
  ) {
    return invalidResponse();
  }
  return {
    createdAt: value.createdAt,
    id: value.id,
    problemVersionId: value.problemVersionId,
    status: value.status,
    studyProfileId: value.studyProfileId,
  };
}

function isStrictContentBlock(value: unknown): value is JourneyContentBlock {
  if (!isObject(value) || typeof value.id !== "string") {
    return false;
  }
  switch (value.type) {
    case "text":
      return hasOnlyKeys(value, ["id", "text", "type"]) && typeof value.text === "string";
    case "inline_math":
    case "display_math":
      return hasOnlyKeys(value, ["id", "latex", "type"]) && typeof value.latex === "string";
    case "rich_line":
      return (
        hasOnlyKeys(value, ["id", "spans", "type"]) &&
        Array.isArray(value.spans) &&
        value.spans.every(
          (span) =>
            isObject(span) &&
            ((span.type === "text" &&
              hasOnlyKeys(span, ["text", "type"]) &&
              typeof span.text === "string") ||
              (span.type === "math" &&
                hasOnlyKeys(span, ["latex", "type"]) &&
                typeof span.latex === "string")),
        )
      );
    case "geometry":
      return (
        hasOnlyKeys(value, ["id", "sceneVersionId", "type"]) &&
        typeof value.sceneVersionId === "string"
      );
    case "image":
      return (
        hasOnlyKeys(value, ["alt", "assetId", "id", "type"]) &&
        typeof value.alt === "string" &&
        typeof value.assetId === "string"
      );
    case "callout":
      return (
        hasOnlyKeys(value, ["content", "id", "kind", "type"]) &&
        (value.kind === "note" ||
          value.kind === "warning" ||
          value.kind === "hint" ||
          value.kind === "success") &&
        isStrictContentBlocks(value.content)
      );
    default:
      return false;
  }
}

export function isStrictContentBlocks(value: unknown): value is JourneyContentBlock[] {
  return Array.isArray(value) && value.every(isStrictContentBlock);
}

function isStrictGeometryAction(value: unknown): value is NextHint["geometryActions"][number] {
  if (!isGeometryAction(value) || !isObject(value)) {
    return false;
  }
  switch (value.type) {
    case "show":
    case "hide":
    case "highlight":
    case "focus":
      return hasOnlyKeys(value, ["objectIds", "type"]);
    case "clear_highlight":
      return hasOnlyKeys(value, ["objectIds", "type"]);
    case "animate":
      return hasOnlyKeys(value, ["animationId", "objectId", "type"]);
    case "ask_select":
      return (
        hasOnlyKeys(value, ["allowedObjectIds", "correctObjectIds", "prompt", "type"]) &&
        isStrictContentBlocks(value.prompt)
      );
  }
}

function isPlanTarget(value: unknown): value is StaticDailyPlan["targets"][number] {
  return (
    isObject(value) &&
    hasOnlyKeys(value, ["cycleCode", "examCycleId", "examName", "priorityRank", "targetId"]) &&
    hasStrings(value, ["cycleCode", "examCycleId", "examName", "targetId"]) &&
    Number.isInteger(value.priorityRank) &&
    Number(value.priorityRank) >= 1
  );
}

function isStudentProblem(value: unknown): value is StaticDailyPlan["items"][number]["problem"] {
  return (
    isObject(value) &&
    hasOnlyKeys(value, [
      "estimatedMinutes",
      "externalCode",
      "geometryScene",
      "problemId",
      "problemVersionId",
      "statement",
      "version",
    ]) &&
    hasStrings(value, ["externalCode", "problemId", "problemVersionId"]) &&
    Number.isInteger(value.estimatedMinutes) &&
    Number(value.estimatedMinutes) >= 1 &&
    Number.isInteger(value.version) &&
    Number(value.version) >= 1 &&
    isStrictContentBlocks(value.statement) &&
    (value.geometryScene === null || isGeometryScene(value.geometryScene))
  );
}

function isPlanItem(value: unknown): value is StaticDailyPlan["items"][number] {
  return (
    isObject(value) &&
    hasOnlyKeys(value, [
      "conceptVersionId",
      "position",
      "problem",
      "selectionReason",
      "supportedTargetIds",
    ]) &&
    isNullableString(value.conceptVersionId) &&
    Number.isInteger(value.position) &&
    (value.selectionReason === "shared_target_foundation" ||
      value.selectionReason === "priority_target_follow_up") &&
    Array.isArray(value.supportedTargetIds) &&
    value.supportedTargetIds.length > 0 &&
    value.supportedTargetIds.every((item) => typeof item === "string") &&
    new Set(value.supportedTargetIds).size === value.supportedTargetIds.length &&
    isStudentProblem(value.problem)
  );
}

function isStaticPlan(value: unknown): value is StaticDailyPlan {
  if (
    !isObject(value) ||
    !hasOnlyKeys(value, ["items", "planDate", "planId", "profileId", "schemaVersion", "targets"]) ||
    value.schemaVersion !== "1.0.0" ||
    !hasStrings(value, ["planDate", "planId", "profileId"]) ||
    !Array.isArray(value.targets) ||
    !value.targets.every(isPlanTarget) ||
    !Array.isArray(value.items) ||
    !value.items.every(isPlanItem)
  ) {
    return false;
  }
  const targetIds = value.targets.map(({ targetId }) => targetId);
  const targetIdSet = new Set(targetIds);
  if (
    targetIdSet.size !== targetIds.length ||
    value.items.some(
      (item, index) =>
        item.position !== index + 1 ||
        item.supportedTargetIds.some((targetId) => !targetIdSet.has(targetId)),
    )
  ) {
    return false;
  }
  return true;
}

function parseStaticPlan(value: unknown): StaticDailyPlan {
  if (!isStaticPlan(value)) {
    return invalidResponse();
  }
  return value;
}

function parseNextHint(value: unknown): NextHint {
  if (
    !isObject(value) ||
    !hasOnlyKeys(value, [
      "conceptVersionId",
      "content",
      "evaluationId",
      "geometryActions",
      "hintEventId",
      "hintId",
      "hintLevel",
      "releasedAt",
      "revealsCompleteSolution",
    ]) ||
    !isNullableString(value.conceptVersionId) ||
    !isStrictContentBlocks(value.content) ||
    value.content.length === 0 ||
    !Array.isArray(value.geometryActions) ||
    !value.geometryActions.every(isStrictGeometryAction) ||
    !hasStrings(value, ["evaluationId", "hintEventId", "hintId", "releasedAt"]) ||
    !Number.isInteger(value.hintLevel) ||
    Number(value.hintLevel) < 1 ||
    typeof value.revealsCompleteSolution !== "boolean"
  ) {
    return invalidResponse();
  }
  return {
    conceptVersionId: value.conceptVersionId,
    content: value.content,
    evaluationId: value.evaluationId,
    geometryActions: value.geometryActions,
    hintEventId: value.hintEventId,
    hintId: value.hintId,
    hintLevel: Number(value.hintLevel),
    releasedAt: value.releasedAt,
    revealsCompleteSolution: value.revealsCompleteSolution,
  };
}

function parseConceptVersion(value: unknown): ConceptVersion {
  if (
    !isObject(value) ||
    !hasOnlyKeys(value, [
      "code",
      "conceptId",
      "conceptVersionId",
      "content",
      "geometryScene",
      "name",
      "version",
    ]) ||
    !hasStrings(value, ["code", "conceptId", "conceptVersionId", "name"]) ||
    !isStrictContentBlocks(value.content) ||
    value.content.length === 0 ||
    (value.geometryScene !== null && !isGeometryScene(value.geometryScene)) ||
    !Number.isInteger(value.version) ||
    Number(value.version) < 1
  ) {
    return invalidResponse();
  }
  return {
    code: value.code,
    conceptId: value.conceptId,
    conceptVersionId: value.conceptVersionId,
    content: value.content,
    geometryScene: value.geometryScene,
    name: value.name,
    version: Number(value.version),
  };
}

export function getStudyProfile(): Promise<StudyProfile> {
  return apiRequest("/api/v1/study-profile", parseStudyProfile);
}

export function createStudyProfile(
  payload: components["schemas"]["StudyProfileCreateRequest"],
): Promise<StudyProfile> {
  return apiRequest("/api/v1/study-profile", parseStudyProfile, {
    body: JSON.stringify(payload),
    method: "POST",
  });
}

export function addExamTarget(
  payload: components["schemas"]["ExamTargetCreateRequest"],
): Promise<ExamTarget> {
  return apiRequest("/api/v1/exam-targets", parseExamTarget, {
    body: JSON.stringify(payload),
    method: "POST",
  });
}

export function getAvailableExamCycles(): Promise<AvailableExamCycles> {
  return apiRequest("/api/v1/exam-cycles", parseAvailableExamCycles);
}

export function getStaticPlan(): Promise<StaticDailyPlan> {
  return apiRequest("/api/v1/plans/today", parseStaticPlan);
}

export function createAttempt(problemVersionId: string): Promise<Attempt> {
  return apiRequest("/api/v1/attempts", parseAttempt, {
    body: JSON.stringify({ problemVersionId }),
    method: "POST",
  });
}

export function requestNextHint(
  attemptId: string,
  idempotencyKey: string = crypto.randomUUID(),
): Promise<NextHint> {
  return apiRequest(`/api/v1/attempts/${attemptId}/hints/next`, parseNextHint, {
    body: JSON.stringify({ idempotencyKey }),
    method: "POST",
  });
}

export function getConceptVersion(conceptVersionId: string): Promise<ConceptVersion> {
  return apiRequest(`/api/v1/concept-versions/${conceptVersionId}`, parseConceptVersion);
}
