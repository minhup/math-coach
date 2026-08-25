import type { components } from "@math-coach/api-client";

export type User = components["schemas"]["UserResponse"];
export type Session = components["schemas"]["SessionResponse"];
export type PresignUploadRequest = components["schemas"]["PresignUploadRequest"];
export type PresignUpload = components["schemas"]["PresignUploadResponse"];
export type Upload = components["schemas"]["UploadResponse"];

export class ApiError extends Error {
  constructor(
    public readonly code: string,
    message: string,
    public readonly status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function invalidResponse(): never {
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

async function readError(response: Response): Promise<ApiError> {
  let payload: unknown;
  try {
    payload = await response.json();
  } catch {
    // The stable fallback prevents upstream HTML or storage errors reaching the UI.
  }
  const error = isObject(payload) && isObject(payload.error) ? payload.error : undefined;
  const code = typeof error?.code === "string" ? error.code : "request_failed";
  const message =
    typeof error?.message === "string" ? error.message : "Something went wrong. Try again.";
  return new ApiError(code, message, response.status);
}

async function apiRequest<T>(
  path: string,
  parse: (value: unknown) => T,
  init?: RequestInit,
): Promise<T> {
  const response = await fetch(path, {
    ...init,
    credentials: "same-origin",
    headers: {
      ...(init?.body ? { "Content-Type": "application/json" } : {}),
      ...init?.headers,
    },
  });
  if (!response.ok) {
    throw await readError(response);
  }
  const payload: unknown = await response.json();
  return parse(payload);
}

async function apiRequestWithoutBody(path: string, init?: RequestInit): Promise<void> {
  const response = await fetch(path, { ...init, credentials: "same-origin" });
  if (!response.ok) {
    throw await readError(response);
  }
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
