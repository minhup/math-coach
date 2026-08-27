import { afterEach, describe, expect, it, vi } from "vitest";

import {
  confirmTranscriptVersion,
  createTranscriptVersion,
  getTranscriptionState,
  getUploadDownload,
  parseTranscriptionResponse,
  parseTranscriptionState,
  requestTranscription,
  type TranscriptDocument,
} from "./transcription-api";

const attemptId = "60000000-0000-4000-8000-000000000001";
const assetId = "60000000-0000-4000-8000-000000000002";
const runId = "60000000-0000-4000-8000-000000000003";
const versionId = "60000000-0000-4000-8000-000000000004";

function run(status = "succeeded") {
  return {
    completedAt: status === "processing" ? null : "2026-08-27T00:00:01Z",
    costUsd: status === "processing" ? null : "0.000000",
    errorCode:
      status === "retryable_failure"
        ? "rate_limited"
        : status === "invalid_schema"
          ? "invalid_schema"
          : null,
    id: runId,
    inputTokens: status === "processing" ? null : 0,
    latencyMs: status === "processing" ? null : 0,
    modelSnapshot: "m6-transcription-fixture-v1",
    outputTokens: status === "processing" ? null : 0,
    pricingVersion: "fake-zero-v1",
    promptHash: "a".repeat(64),
    promptVersion: "m6-faithful-transcription-v1",
    provider: "application-owned-deterministic-fake",
    schemaAttempts: status === "processing" ? 0 : status === "invalid_schema" ? 2 : 1,
    schemaVersion: "m6-provider-transcript-v1",
    startedAt: "2026-08-27T00:00:00Z",
    status,
  };
}

const document: TranscriptDocument = {
  attemptId,
  blocks: [
    {
      id: "m6-text-1",
      sourceRegion: {
        attemptAssetId: assetId,
        height: 0.1,
        units: "normalized",
        width: 0.4,
        x: 0.1,
        y: 0.2,
      },
      text: "Em giữ nguyên lỗi dấu: ",
      type: "text",
    },
    { id: "m6-math-1", latex: "x=-2", type: "math" },
  ],
  schemaVersion: "3.0.0",
  warnings: [
    {
      blockId: "m6-math-1",
      code: "low_confidence_math",
      message: "A formula may need review.",
    },
  ],
};

function version() {
  return {
    attemptId,
    createdAt: "2026-08-27T00:00:01Z",
    document,
    id: versionId,
    origin: "provider",
    parentTranscriptVersionId: null,
    sourceRunId: runId,
    transcriptHash: "b".repeat(64),
    version: 1,
  };
}

afterEach(() => vi.restoreAllMocks());

describe("transcription API boundary", () => {
  it("accepts one complete strict mixed transcript only after all nested data validates", () => {
    expect(
      parseTranscriptionResponse({
        outcome: "ready",
        run: run(),
        transcriptVersion: version(),
      }),
    ).toMatchObject({ transcriptVersion: { document: { attemptId } } });
  });

  it.each([
    { ...document, markdown: "**raw**" },
    {
      ...document,
      blocks: [{ html: "<script>bad()</script>", id: "bad", text: "bad", type: "text" }],
    },
    {
      ...document,
      blocks: [
        {
          id: "bad-region",
          sourceRegion: {
            attemptAssetId: assetId,
            height: 0.2,
            units: "normalized",
            width: 0.2,
            x: 0.9,
            y: 0,
          },
          text: "outside",
          type: "text",
        },
      ],
    },
    {
      ...document,
      warnings: [
        {
          code: "low_confidence_math",
          message: "Provider-controlled warning",
        },
      ],
    },
  ])("rejects malformed nested transcript data before rendering", (malformed) => {
    expect(() =>
      parseTranscriptionResponse({
        outcome: "ready",
        run: run(),
        transcriptVersion: { ...version(), document: malformed },
      }),
    ).toThrow(expect.objectContaining({ code: "invalid_response", status: 502 }));
  });

  it("accepts uncertainty without a transcript and rejects an invented uncertain document", () => {
    const uncertainRun = { ...run("uncertain"), errorCode: null, status: "uncertain" };
    const warning = {
      code: "ordering_uncertain",
      message: "The reading order may need review.",
    };
    expect(
      parseTranscriptionResponse({ outcome: "uncertain", run: uncertainRun, warnings: [warning] }),
    ).toMatchObject({ outcome: "uncertain" });
    expect(() =>
      parseTranscriptionResponse({
        outcome: "uncertain",
        run: uncertainRun,
        transcriptVersion: version(),
        warnings: [warning],
      }),
    ).toThrow(expect.objectContaining({ code: "invalid_response" }));
  });

  it("distinguishes processing, retryable, permanent, invalid-schema, and ready reload states", () => {
    expect(parseTranscriptionState({ run: run("processing"), status: "processing" }).status).toBe(
      "processing",
    );
    for (const status of ["retryable_failure", "invalid_schema"] as const) {
      expect(parseTranscriptionState({ run: run(status), status }).status).toBe(status);
    }
    expect(
      parseTranscriptionState({
        run: { ...run("permanent_failure"), errorCode: "provider_rejected" },
        status: "permanent_failure",
      }).status,
    ).toBe("permanent_failure");
    expect(
      parseTranscriptionState({
        confirmation: null,
        run: run(),
        status: "ready",
        transcriptVersion: version(),
      }).status,
    ).toBe("ready");
  });

  it("sends only application-owned request fields and exact version identities", async () => {
    const confirmation = {
      attemptId,
      confirmedAt: "2026-08-27T00:00:02Z",
      id: "60000000-0000-4000-8000-000000000005",
      transcriptHash: "b".repeat(64),
      transcriptVersionId: versionId,
    };
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({ outcome: "ready", run: run(), transcriptVersion: version() }),
        ),
      )
      .mockResolvedValueOnce(new Response(JSON.stringify(version())))
      .mockResolvedValueOnce(new Response(JSON.stringify(confirmation)))
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            downloadUrl: "http://storage.test/synthetic?signature=application-owned",
            expiresAt: "2026-08-27T00:05:00Z",
            uploadId: "upload-1",
          }),
        ),
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            confirmation: null,
            run: run(),
            status: "ready",
            transcriptVersion: version(),
          }),
        ),
      );

    await requestTranscription(attemptId, "upload-1", "idempotency-1");
    await createTranscriptVersion(attemptId, versionId, document);
    await confirmTranscriptVersion(attemptId, versionId, "b".repeat(64));
    await getUploadDownload("upload-1");
    await getTranscriptionState(attemptId);

    expect(fetchMock).toHaveBeenNthCalledWith(
      1,
      `/api/v1/attempts/${attemptId}/transcribe`,
      expect.objectContaining({
        body: JSON.stringify({ idempotencyKey: "idempotency-1", uploadId: "upload-1" }),
      }),
    );
    expect(fetchMock).toHaveBeenNthCalledWith(
      3,
      `/api/v1/attempts/${attemptId}/confirm-transcript`,
      expect.objectContaining({
        body: JSON.stringify({ transcriptHash: "b".repeat(64), transcriptVersionId: versionId }),
      }),
    );
  });
});
