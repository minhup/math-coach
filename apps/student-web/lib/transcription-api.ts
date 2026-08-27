import type { components } from "@math-coach/api-client";

import { validateTranscriptState } from "../features/transcription/transcript-state";
import { invalidResponse } from "./api";
import { apiRequest } from "./api-transport";

export type TranscriptionResponse =
  | components["schemas"]["ReadyTranscriptionResponse"]
  | components["schemas"]["UncertainTranscriptionResponse"];
export type TranscriptionState =
  | components["schemas"]["TranscriptionNotStartedState"]
  | components["schemas"]["TranscriptionProcessingState"]
  | components["schemas"]["TranscriptionReadyState"]
  | components["schemas"]["TranscriptionUncertainState"]
  | components["schemas"]["TranscriptionFailureState"];
export type TranscriptionRun = components["schemas"]["TranscriptionRunResponse"];
export type TranscriptDocument = components["schemas"]["TranscriptDocument"];
export type TranscriptVersion = components["schemas"]["TranscriptVersionResponse"];
export type TranscriptConfirmation = components["schemas"]["TranscriptConfirmationResponse"];
export type UploadDownload = components["schemas"]["UploadDownloadResponse"];

type TranscriptBlock = TranscriptDocument["blocks"][number];
type TranscriptWarning = TranscriptDocument["warnings"][number];
type SourceRegion = components["schemas"]["SourceRegion"];

const warningMessages: Record<TranscriptWarning["code"], string> = {
  ambiguous_cross_out: "A crossed-out part may need review.",
  ambiguous_insertion: "An inserted part may need review.",
  low_confidence_math: "A formula may need review.",
  low_confidence_text: "Some text may need review.",
  ordering_uncertain: "The reading order may need review.",
  source_region_unavailable: "A source location is unavailable.",
};

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function hasOnlyKeys(value: Record<string, unknown>, keys: readonly string[]): boolean {
  return Object.keys(value).every((key) => keys.includes(key));
}

function hasStrings(value: Record<string, unknown>, keys: readonly string[]): boolean {
  return keys.every((key) => typeof value[key] === "string" && value[key].length > 0);
}

function isNullableString(value: unknown): value is string | null {
  return value === null || typeof value === "string";
}

function isNullableNonnegativeInteger(value: unknown): value is number | null {
  return value === null || (Number.isInteger(value) && Number(value) >= 0);
}

function isWarningCode(value: unknown): value is TranscriptWarning["code"] {
  return typeof value === "string" && value in warningMessages;
}

function isSourceRegion(value: unknown): value is SourceRegion {
  if (
    !isObject(value) ||
    !hasOnlyKeys(value, ["attemptAssetId", "height", "units", "width", "x", "y"]) ||
    typeof value.attemptAssetId !== "string" ||
    value.attemptAssetId.length === 0 ||
    value.units !== "normalized" ||
    ![value.x, value.y, value.width, value.height].every(
      (coordinate) => typeof coordinate === "number" && Number.isFinite(coordinate),
    )
  ) {
    return false;
  }
  return (
    Number(value.x) >= 0 &&
    Number(value.y) >= 0 &&
    Number(value.width) > 0 &&
    Number(value.height) > 0 &&
    Number(value.x) + Number(value.width) <= 1 &&
    Number(value.y) + Number(value.height) <= 1
  );
}

function isTranscriptBlock(value: unknown): value is TranscriptBlock {
  if (
    !isObject(value) ||
    typeof value.id !== "string" ||
    value.id.length === 0 ||
    !(
      value.sourceRegion === undefined ||
      value.sourceRegion === null ||
      isSourceRegion(value.sourceRegion)
    )
  ) {
    return false;
  }
  if (value.type === "text") {
    return (
      hasOnlyKeys(value, ["id", "sourceRegion", "text", "type"]) && typeof value.text === "string"
    );
  }
  return (
    value.type === "math" &&
    hasOnlyKeys(value, ["id", "latex", "sourceRegion", "type"]) &&
    typeof value.latex === "string"
  );
}

function isTranscriptWarning(value: unknown): value is TranscriptWarning {
  if (
    !isObject(value) ||
    !hasOnlyKeys(value, ["blockId", "code", "message"]) ||
    !isWarningCode(value.code) ||
    typeof value.message !== "string" ||
    (value.blockId !== undefined && value.blockId !== null && typeof value.blockId !== "string")
  ) {
    return false;
  }
  return value.message === warningMessages[value.code];
}

function isTranscriptDocument(value: unknown): value is TranscriptDocument {
  if (
    !isObject(value) ||
    !hasOnlyKeys(value, ["attemptId", "blocks", "schemaVersion", "warnings"]) ||
    typeof value.attemptId !== "string" ||
    value.attemptId.length === 0 ||
    value.schemaVersion !== "3.0.0" ||
    !Array.isArray(value.blocks) ||
    value.blocks.length === 0 ||
    !value.blocks.every(isTranscriptBlock) ||
    !Array.isArray(value.warnings) ||
    !value.warnings.every(isTranscriptWarning)
  ) {
    return false;
  }
  const ids = value.blocks.map(({ id }) => id);
  const known = new Set(ids);
  return (
    ids.length === known.size &&
    value.warnings.every(
      ({ blockId }) => blockId === undefined || blockId === null || known.has(blockId),
    )
  );
}

function isRun(value: unknown): value is TranscriptionRun {
  if (
    !isObject(value) ||
    !hasOnlyKeys(value, [
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
      "schemaAttempts",
      "schemaVersion",
      "startedAt",
      "status",
    ]) ||
    !hasStrings(value, [
      "id",
      "modelSnapshot",
      "pricingVersion",
      "promptVersion",
      "provider",
      "schemaVersion",
      "startedAt",
    ]) ||
    typeof value.promptHash !== "string" ||
    !/^[0-9a-f]{64}$/.test(value.promptHash) ||
    ![
      "processing",
      "succeeded",
      "uncertain",
      "retryable_failure",
      "permanent_failure",
      "invalid_schema",
    ].includes(String(value.status)) ||
    !Number.isInteger(value.schemaAttempts) ||
    Number(value.schemaAttempts) < 0 ||
    Number(value.schemaAttempts) > 2 ||
    !isNullableString(value.completedAt) ||
    !isNullableString(value.errorCode) ||
    !isNullableNonnegativeInteger(value.latencyMs) ||
    !isNullableNonnegativeInteger(value.inputTokens) ||
    !isNullableNonnegativeInteger(value.outputTokens) ||
    !(
      value.costUsd === null ||
      (typeof value.costUsd === "string" && /^\d+(?:\.\d+)?$/.test(value.costUsd))
    )
  ) {
    return false;
  }
  if (value.status === "processing") {
    return (
      value.completedAt === null &&
      value.costUsd === null &&
      value.errorCode === null &&
      value.inputTokens === null &&
      value.latencyMs === null &&
      value.outputTokens === null &&
      value.schemaAttempts === 0
    );
  }
  const failure = ["retryable_failure", "permanent_failure", "invalid_schema"].includes(
    String(value.status),
  );
  return (
    value.completedAt !== null &&
    value.costUsd !== null &&
    value.inputTokens !== null &&
    value.latencyMs !== null &&
    value.outputTokens !== null &&
    (failure ? value.errorCode !== null : value.errorCode === null)
  );
}

function isTranscriptVersion(value: unknown): value is TranscriptVersion {
  if (
    !isObject(value) ||
    !hasOnlyKeys(value, [
      "attemptId",
      "createdAt",
      "document",
      "id",
      "origin",
      "parentTranscriptVersionId",
      "sourceRunId",
      "transcriptHash",
      "version",
    ]) ||
    !hasStrings(value, ["attemptId", "createdAt", "id", "sourceRunId"]) ||
    (value.origin !== "provider" && value.origin !== "learner") ||
    !isNullableString(value.parentTranscriptVersionId) ||
    typeof value.transcriptHash !== "string" ||
    !/^[0-9a-f]{64}$/.test(value.transcriptHash) ||
    !Number.isInteger(value.version) ||
    Number(value.version) < 1 ||
    !isTranscriptDocument(value.document) ||
    value.document.attemptId !== value.attemptId
  ) {
    return false;
  }
  try {
    validateTranscriptState(value.document);
    return true;
  } catch {
    return false;
  }
}

function isConfirmation(value: unknown): value is TranscriptConfirmation {
  return (
    isObject(value) &&
    hasOnlyKeys(value, [
      "attemptId",
      "confirmedAt",
      "id",
      "transcriptHash",
      "transcriptVersionId",
    ]) &&
    hasStrings(value, ["attemptId", "confirmedAt", "id", "transcriptVersionId"]) &&
    typeof value.transcriptHash === "string" &&
    /^[0-9a-f]{64}$/.test(value.transcriptHash)
  );
}

function isReadyResponse(
  value: unknown,
): value is components["schemas"]["ReadyTranscriptionResponse"] {
  return (
    isObject(value) &&
    hasOnlyKeys(value, ["outcome", "run", "transcriptVersion"]) &&
    value.outcome === "ready" &&
    isRun(value.run) &&
    value.run.status === "succeeded" &&
    isTranscriptVersion(value.transcriptVersion) &&
    value.transcriptVersion.sourceRunId === value.run.id
  );
}

function isUncertainResponse(
  value: unknown,
): value is components["schemas"]["UncertainTranscriptionResponse"] {
  return (
    isObject(value) &&
    hasOnlyKeys(value, ["outcome", "run", "warnings"]) &&
    value.outcome === "uncertain" &&
    isRun(value.run) &&
    value.run.status === "uncertain" &&
    Array.isArray(value.warnings) &&
    value.warnings.length > 0 &&
    value.warnings.every(isTranscriptWarning) &&
    value.warnings.every(({ blockId }) => blockId === undefined || blockId === null)
  );
}

export function parseTranscriptionResponse(value: unknown): TranscriptionResponse {
  if (isReadyResponse(value) || isUncertainResponse(value)) {
    return value;
  }
  return invalidResponse();
}

function parseTranscriptVersion(value: unknown): TranscriptVersion {
  return isTranscriptVersion(value) ? value : invalidResponse();
}

function parseConfirmation(value: unknown): TranscriptConfirmation {
  return isConfirmation(value) ? value : invalidResponse();
}

function isNotStartedState(
  value: unknown,
): value is components["schemas"]["TranscriptionNotStartedState"] {
  return isObject(value) && value.status === "not_started" && hasOnlyKeys(value, ["status"]);
}

function isProcessingState(
  value: unknown,
): value is components["schemas"]["TranscriptionProcessingState"] {
  return (
    isObject(value) &&
    value.status === "processing" &&
    hasOnlyKeys(value, ["run", "status"]) &&
    isRun(value.run) &&
    value.run.status === "processing"
  );
}

function isReadyState(value: unknown): value is components["schemas"]["TranscriptionReadyState"] {
  if (!isObject(value) || value.status !== "ready") {
    return false;
  }
  if (
    !hasOnlyKeys(value, ["confirmation", "run", "status", "transcriptVersion"]) ||
    !isRun(value.run) ||
    value.run.status !== "succeeded" ||
    !isTranscriptVersion(value.transcriptVersion) ||
    !(value.confirmation === null || isConfirmation(value.confirmation))
  ) {
    return false;
  }
  return (
    value.confirmation === null ||
    (value.confirmation.attemptId === value.transcriptVersion.attemptId &&
      value.confirmation.transcriptVersionId === value.transcriptVersion.id &&
      value.confirmation.transcriptHash === value.transcriptVersion.transcriptHash)
  );
}

function isUncertainState(
  value: unknown,
): value is components["schemas"]["TranscriptionUncertainState"] {
  return (
    isObject(value) &&
    value.status === "uncertain" &&
    hasOnlyKeys(value, ["run", "status", "warnings"]) &&
    isRun(value.run) &&
    value.run.status === "uncertain" &&
    Array.isArray(value.warnings) &&
    value.warnings.length > 0 &&
    value.warnings.every(isTranscriptWarning)
  );
}

function isFailureState(
  value: unknown,
): value is components["schemas"]["TranscriptionFailureState"] {
  return (
    isObject(value) &&
    (value.status === "retryable_failure" ||
      value.status === "permanent_failure" ||
      value.status === "invalid_schema") &&
    hasOnlyKeys(value, ["run", "status"]) &&
    isRun(value.run) &&
    value.run.status === value.status
  );
}

export function parseTranscriptionState(value: unknown): TranscriptionState {
  if (
    isNotStartedState(value) ||
    isProcessingState(value) ||
    isReadyState(value) ||
    isUncertainState(value) ||
    isFailureState(value)
  ) {
    return value;
  }
  return invalidResponse();
}

function isUploadDownload(value: unknown): value is UploadDownload {
  if (
    !isObject(value) ||
    !hasOnlyKeys(value, ["downloadUrl", "expiresAt", "uploadId"]) ||
    typeof value.downloadUrl !== "string" ||
    value.downloadUrl.length === 0 ||
    typeof value.expiresAt !== "string" ||
    value.expiresAt.length === 0 ||
    typeof value.uploadId !== "string" ||
    value.uploadId.length === 0
  ) {
    return false;
  }
  try {
    const parsed = new URL(value.downloadUrl);
    if (parsed.protocol !== "http:" && parsed.protocol !== "https:") {
      return false;
    }
  } catch {
    return false;
  }
  return true;
}

function parseUploadDownload(value: unknown): UploadDownload {
  return isUploadDownload(value) ? value : invalidResponse();
}

export function requestTranscription(
  attemptId: string,
  uploadId: string,
  idempotencyKey: string,
): Promise<TranscriptionResponse> {
  return apiRequest(`/api/v1/attempts/${attemptId}/transcribe`, parseTranscriptionResponse, {
    body: JSON.stringify({ idempotencyKey, uploadId }),
    method: "POST",
  });
}

export function getTranscriptionState(attemptId: string): Promise<TranscriptionState> {
  return apiRequest(`/api/v1/attempts/${attemptId}/transcription`, parseTranscriptionState);
}

export function createTranscriptVersion(
  attemptId: string,
  baseTranscriptVersionId: string,
  document: TranscriptDocument,
): Promise<TranscriptVersion> {
  const validated = validateTranscriptState(document);
  return apiRequest(`/api/v1/attempts/${attemptId}/transcripts`, parseTranscriptVersion, {
    body: JSON.stringify({ baseTranscriptVersionId, document: validated }),
    method: "POST",
  });
}

export function confirmTranscriptVersion(
  attemptId: string,
  transcriptVersionId: string,
  transcriptHash: string,
): Promise<TranscriptConfirmation> {
  return apiRequest(`/api/v1/attempts/${attemptId}/confirm-transcript`, parseConfirmation, {
    body: JSON.stringify({ transcriptHash, transcriptVersionId }),
    method: "POST",
  });
}

export function getUploadDownload(uploadId: string): Promise<UploadDownload> {
  return apiRequest(`/api/v1/uploads/${uploadId}/download-url`, parseUploadDownload, {
    method: "POST",
  });
}
