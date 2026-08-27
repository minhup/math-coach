import type { components } from "@math-coach/api-client";

import { validateAndOrderGeometryScene } from "../features/geometry/geometry-scene";
import { validateGeometryAction } from "../features/geometry/interaction-state";
import { ApiError, apiRequest, apiRequestWithoutBody } from "./api-transport";

export { ApiError } from "./api-transport";

export type User = components["schemas"]["UserResponse"];
export type Session = components["schemas"]["SessionResponse"];
export type PresignUploadRequest = components["schemas"]["PresignUploadRequest"];
export type PresignUpload = components["schemas"]["PresignUploadResponse"];
export type Upload = components["schemas"]["UploadResponse"];
export type ContentPreviewList = components["schemas"]["ContentPreviewListResponse"];
export type ContentPreview = components["schemas"]["ContentPreviewResponse"];
export type ContentBlock = ContentPreview["statement"][number];
export type GeometryAction = ContentPreview["hints"][number]["geometryActions"][number];
export type GeometryScene = NonNullable<ContentPreview["geometryScene"]>;

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function isStringArray(value: unknown): value is string[] {
  return Array.isArray(value) && value.every((item) => typeof item === "string");
}

function hasStringProperties(value: Record<string, unknown>, properties: string[]): boolean {
  return properties.every((property) => typeof value[property] === "string");
}

function isNullableString(value: unknown): value is string | null {
  return value === null || typeof value === "string";
}

export function invalidResponse(): never {
  throw new ApiError(
    "invalid_response",
    "The service returned an unexpected response. Try again.",
    502,
  );
}

function parseUser(value: unknown): User {
  if (!isObject(value) || typeof value.id !== "string" || typeof value.displayName !== "string") {
    return invalidResponse();
  }
  return { displayName: value.displayName, id: value.id };
}

function parseSession(value: unknown): Session {
  if (!isObject(value) || typeof value.expiresAt !== "string") {
    return invalidResponse();
  }
  return { expiresAt: value.expiresAt, user: parseUser(value.user) };
}

function parsePresignUpload(value: unknown): PresignUpload {
  if (
    !isObject(value) ||
    typeof value.expiresAt !== "string" ||
    typeof value.uploadId !== "string" ||
    typeof value.uploadUrl !== "string"
  ) {
    return invalidResponse();
  }
  return {
    expiresAt: value.expiresAt,
    uploadId: value.uploadId,
    uploadUrl: value.uploadUrl,
  };
}

function parseUpload(value: unknown): Upload {
  if (
    !isObject(value) ||
    (value.contentType !== "image/jpeg" &&
      value.contentType !== "image/png" &&
      value.contentType !== "image/webp") ||
    typeof value.createdAt !== "string" ||
    typeof value.fileName !== "string" ||
    typeof value.id !== "string" ||
    typeof value.sizeBytes !== "number" ||
    (value.status !== "pending" && value.status !== "ready" && value.status !== "rejected")
  ) {
    return invalidResponse();
  }
  return {
    contentType: value.contentType,
    createdAt: value.createdAt,
    fileName: value.fileName,
    id: value.id,
    sizeBytes: value.sizeBytes,
    status: value.status,
  };
}

function isProvenance(value: unknown): value is components["schemas"]["Provenance"] {
  if (!isObject(value)) {
    return false;
  }
  return (
    hasStringProperties(value, [
      "acquiredBy",
      "acquisitionDate",
      "attributionText",
      "creator",
      "mathematicsReviewedAt",
      "mathematicsReviewer",
      "publicationDate",
      "rightsEvidence",
      "rightsReviewedAt",
      "rightsReviewer",
      "sourceReference",
      "title",
    ]) &&
    isNullableString(value.adaptationDescription) &&
    isNullableString(value.translationDescription) &&
    isStringArray(value.derivativeOf) &&
    isStringArray(value.permittedUses) &&
    isStringArray(value.restrictions) &&
    value.publicationStatus === "synthetic_only" &&
    value.rightsBasis === "original_fixture" &&
    value.sourceKind === "original_synthetic"
  );
}

export function isContentBlock(value: unknown): value is ContentBlock {
  if (!isObject(value) || typeof value.id !== "string") {
    return false;
  }
  switch (value.type) {
    case "text":
      return typeof value.text === "string";
    case "inline_math":
    case "display_math":
      return typeof value.latex === "string";
    case "rich_line":
      return (
        Array.isArray(value.spans) &&
        value.spans.every(
          (span) =>
            isObject(span) &&
            ((span.type === "text" && typeof span.text === "string") ||
              (span.type === "math" && typeof span.latex === "string")),
        )
      );
    case "geometry":
      return typeof value.sceneVersionId === "string";
    case "image":
      return typeof value.alt === "string" && typeof value.assetId === "string";
    case "callout":
      return (
        ["note", "warning", "hint", "success"].includes(String(value.kind)) &&
        Array.isArray(value.content) &&
        value.content.every(isContentBlock)
      );
    default:
      return false;
  }
}

export function isContentBlocks(value: unknown): value is ContentBlock[] {
  return Array.isArray(value) && value.every(isContentBlock);
}

export function isGeometryAction(value: unknown): value is GeometryAction {
  if (!isObject(value)) {
    return false;
  }
  switch (value.type) {
    case "show":
    case "hide":
    case "highlight":
    case "focus":
      return isStringArray(value.objectIds);
    case "clear_highlight":
      return (
        value.objectIds === undefined || value.objectIds === null || isStringArray(value.objectIds)
      );
    case "animate":
      return typeof value.animationId === "string" && typeof value.objectId === "string";
    case "ask_select":
      return (
        isStringArray(value.allowedObjectIds) &&
        (value.correctObjectIds === undefined ||
          value.correctObjectIds === null ||
          isStringArray(value.correctObjectIds)) &&
        isContentBlocks(value.prompt)
      );
    default:
      return false;
  }
}

export function isGeometryScene(
  value: unknown,
): value is components["schemas"]["GeometrySceneVersion"] {
  try {
    validateAndOrderGeometryScene(value);
    return true;
  } catch {
    return false;
  }
}

function isContentPreviewSummary(
  value: unknown,
): value is components["schemas"]["ContentPreviewSummary"] {
  return (
    isObject(value) &&
    hasStringProperties(value, ["externalCode", "problemId", "problemVersionId"]) &&
    typeof value.supportedExamCount === "number" &&
    typeof value.version === "number"
  );
}

function isContentPreviewList(value: unknown): value is ContentPreviewList {
  return (
    isObject(value) && Array.isArray(value.items) && value.items.every(isContentPreviewSummary)
  );
}

function parseContentPreviewList(value: unknown): ContentPreviewList {
  if (!isContentPreviewList(value)) {
    return invalidResponse();
  }
  return value;
}

function isExamRelevance(value: unknown): value is components["schemas"]["PreviewExamRelevance"] {
  return (
    isObject(value) &&
    hasStringProperties(value, [
      "cycleCode",
      "examCode",
      "examCycleId",
      "examDate",
      "examId",
      "examName",
      "relevanceNote",
    ]) &&
    ["low", "medium", "high"].includes(String(value.relevanceLevel))
  );
}

function isSkillLink(value: unknown): value is components["schemas"]["PreviewSkillLink"] {
  return (
    isObject(value) &&
    hasStringProperties(value, ["importance", "skillCode", "skillId", "skillName"]) &&
    ["primary", "secondary", "prerequisite", "diagnostic"].includes(String(value.role))
  );
}

function isReferenceSolution(
  value: unknown,
): value is components["schemas"]["PreviewReferenceSolution"] {
  return (
    isObject(value) &&
    hasStringProperties(value, ["id", "methodLabel", "solutionCode"]) &&
    value.expertVerified === true &&
    value.nonExhaustive === true &&
    isContentBlocks(value.content)
  );
}

function isRubricItem(value: unknown): value is components["schemas"]["PreviewRubricItem"] {
  return (
    isObject(value) &&
    hasStringProperties(value, ["id", "maximumScore", "rubricCode", "skillId"]) &&
    typeof value.orderIndex === "number" &&
    isContentBlocks(value.description)
  );
}

function isHint(value: unknown): value is components["schemas"]["PreviewHint"] {
  return (
    isObject(value) &&
    typeof value.id === "string" &&
    isNullableString(value.conceptId) &&
    typeof value.hintLevel === "number" &&
    typeof value.revealsCompleteSolution === "boolean" &&
    isContentBlocks(value.content) &&
    Array.isArray(value.geometryActions) &&
    value.geometryActions.every(isGeometryAction)
  );
}

function isContentPreview(value: unknown): value is ContentPreview {
  return (
    isObject(value) &&
    hasStringProperties(value, ["externalCode", "maximumScore", "problemId", "problemVersionId"]) &&
    ["introductory", "core", "advanced", "challenge"].includes(String(value.difficultyBand)) &&
    typeof value.estimatedMinutes === "number" &&
    typeof value.version === "number" &&
    isProvenance(value.provenance) &&
    isContentBlocks(value.statement) &&
    Array.isArray(value.supportedExams) &&
    value.supportedExams.every(isExamRelevance) &&
    Array.isArray(value.skills) &&
    value.skills.every(isSkillLink) &&
    Array.isArray(value.referenceSolutions) &&
    value.referenceSolutions.every(isReferenceSolution) &&
    Array.isArray(value.rubric) &&
    value.rubric.every(isRubricItem) &&
    Array.isArray(value.hints) &&
    value.hints.every(isHint) &&
    (value.geometryScene === null || isGeometryScene(value.geometryScene))
  );
}

function parseContentPreview(value: unknown): ContentPreview {
  if (!isContentPreview(value)) {
    return invalidResponse();
  }
  if (value.geometryScene === null) {
    if (value.hints.some((hint) => hint.geometryActions.length > 0)) {
      return invalidResponse();
    }
    return value;
  }
  const scene = validateAndOrderGeometryScene(value.geometryScene);
  if (
    value.hints.some((hint) =>
      hint.geometryActions.some((action) => validateGeometryAction(scene, action) === null),
    )
  ) {
    return invalidResponse();
  }
  return value;
}

export function getCurrentUser(): Promise<User> {
  return apiRequest("/api/v1/auth/me", parseUser);
}

export function login(inviteCode: string): Promise<Session> {
  return apiRequest("/api/v1/auth/pilot-login", parseSession, {
    body: JSON.stringify({ inviteCode }),
    method: "POST",
  });
}

export function logout(): Promise<void> {
  return apiRequestWithoutBody("/api/v1/auth/logout", { method: "POST" });
}

export function presignUpload(payload: PresignUploadRequest): Promise<PresignUpload> {
  return apiRequest("/api/v1/uploads/presign", parsePresignUpload, {
    body: JSON.stringify(payload),
    method: "POST",
  });
}

export async function putSignedUpload(url: string, file: File): Promise<void> {
  const response = await fetch(url, {
    body: file,
    headers: { "Content-Type": file.type },
    method: "PUT",
  });
  if (!response.ok) {
    throw new ApiError(
      "upload_transfer_failed",
      "The image could not be uploaded.",
      response.status,
    );
  }
}

export function completeUpload(uploadId: string): Promise<Upload> {
  return apiRequest(`/api/v1/uploads/${uploadId}/complete`, parseUpload, { method: "POST" });
}

export function getContentPreviews(): Promise<ContentPreviewList> {
  return apiRequest("/api/v1/internal/content-preview", parseContentPreviewList);
}

export function getContentPreview(problemId: string): Promise<ContentPreview> {
  return apiRequest(`/api/v1/internal/content-preview/${problemId}`, parseContentPreview);
}
