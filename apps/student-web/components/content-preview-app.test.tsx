import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ContentPreviewApp } from "./content-preview-app";

function jsonResponse(payload: object, status = 200): Response {
  return new Response(JSON.stringify(payload), {
    headers: { "Content-Type": "application/json" },
    status,
  });
}

const provenance = {
  acquiredBy: "Math Coach development",
  acquisitionDate: "2026-08-26",
  adaptationDescription: null,
  attributionText: "Original synthetic Math Coach fixture.",
  creator: "Math Coach fixture author",
  derivativeOf: [],
  mathematicsReviewedAt: "2026-08-26",
  mathematicsReviewer: "Synthetic fixture reviewer",
  permittedUses: ["internal_development"],
  publicationDate: "2026-08-26",
  publicationStatus: "synthetic_only",
  restrictions: ["not_real_exam_content"],
  rightsBasis: "original_fixture",
  rightsEvidence: "Created for testing.",
  rightsReviewedAt: "2026-08-26",
  rightsReviewer: "Synthetic fixture reviewer",
  sourceKind: "original_synthetic",
  sourceReference: "repo://synthetic",
  title: "Synthetic problem",
  translationDescription: null,
};

const summary = {
  externalCode: "SYN-M2-GEO-001",
  problemId: "problem-1",
  problemVersionId: "problem-version-1",
  supportedExamCount: 2,
  version: 1,
};

const preview = {
  difficultyBand: "core",
  estimatedMinutes: 12,
  externalCode: "SYN-M2-GEO-001",
  geometryScene: null,
  hints: [],
  maximumScore: "4.00",
  problemId: "problem-1",
  problemVersionId: "problem-version-1",
  provenance,
  referenceSolutions: [],
  rubric: [],
  skills: [],
  statement: [{ id: "statement", text: "Synthetic statement.", type: "text" }],
  supportedExams: [],
  version: 1,
};

afterEach(() => {
  vi.restoreAllMocks();
});

describe("ContentPreviewApp", () => {
  it("shows loading followed by an explicit empty state", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(jsonResponse({ items: [] }));

    render(<ContentPreviewApp />);

    expect(screen.getByText("Loading validated content…")).toBeInTheDocument();
    expect(
      await screen.findByRole("heading", { name: "No validated content" }),
    ).toBeInTheDocument();
  });

  it("shows a safe authorization state", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      jsonResponse(
        { error: { code: "authentication_required", message: "Authentication required." } },
        401,
      ),
    );

    render(<ContentPreviewApp />);

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Sign in to inspect internal content.",
    );
  });

  it("loads the first immutable problem preview", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(jsonResponse({ items: [summary] }))
      .mockResolvedValueOnce(jsonResponse(preview));

    render(<ContentPreviewApp />);

    expect(await screen.findByRole("heading", { name: "SYN-M2-GEO-001" })).toBeInTheDocument();
    expect(fetchMock).toHaveBeenNthCalledWith(
      2,
      "/api/v1/internal/content-preview/problem-1",
      expect.objectContaining({ credentials: "same-origin" }),
    );
  });

  it("retries a temporary API failure", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(
        jsonResponse({ error: { code: "storage_unavailable", message: "Try shortly." } }, 503),
      )
      .mockResolvedValueOnce(jsonResponse({ items: [] }));
    const user = userEvent.setup();

    render(<ContentPreviewApp />);

    expect(await screen.findByRole("alert")).toHaveTextContent("Try shortly.");
    await user.click(screen.getByRole("button", { name: "Try again" }));

    expect(
      await screen.findByRole("heading", { name: "No validated content" }),
    ).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });
});
