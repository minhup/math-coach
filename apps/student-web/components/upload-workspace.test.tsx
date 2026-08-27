import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { UploadWorkspace } from "./upload-workspace";

function jsonResponse(payload: object, status = 200): Response {
  return new Response(JSON.stringify(payload), {
    headers: { "Content-Type": "application/json" },
    status,
  });
}

beforeEach(() => {
  Object.defineProperty(URL, "createObjectURL", {
    configurable: true,
    value: vi.fn(() => "blob:synthetic-preview"),
  });
  Object.defineProperty(URL, "revokeObjectURL", {
    configurable: true,
    value: vi.fn(),
  });
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe("UploadWorkspace", () => {
  it("previews and completes a signed synthetic-image upload", async () => {
    const uploadId = "1583b8ad-6328-4b22-9dbd-a46c9ca7168d";
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(
        jsonResponse({
          expiresAt: "2026-08-25T10:05:00Z",
          uploadId,
          uploadUrl: "http://storage.test/signed-upload",
        }),
      )
      .mockResolvedValueOnce(new Response(null, { status: 200 }))
      .mockResolvedValueOnce(
        jsonResponse({
          contentType: "image/png",
          createdAt: "2026-08-25T10:00:00Z",
          fileName: "synthetic-solution.png",
          id: uploadId,
          sizeBytes: 4,
          status: "ready",
        }),
      );
    const user = userEvent.setup();
    const onContinue = vi.fn();
    const file = new File([new Uint8Array([1, 2, 3, 4])], "synthetic-solution.png", {
      type: "image/png",
    });
    render(<UploadWorkspace onContinue={onContinue} />);

    await user.upload(screen.getByLabelText("Choose image"), file);
    expect(screen.getByAltText("Preview of the selected paper solution")).toBeInTheDocument();
    expect(screen.getByText("synthetic-solution.png")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Upload solution" }));

    expect(await screen.findByText("Image received and verified")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Use this upload" }));
    expect(onContinue).toHaveBeenCalledWith(
      expect.objectContaining({ id: uploadId, status: "ready" }),
    );
    expect(fetchMock).toHaveBeenNthCalledWith(
      2,
      "http://storage.test/signed-upload",
      expect.objectContaining({ method: "PUT" }),
    );
    expect(fetchMock).toHaveBeenNthCalledWith(
      3,
      `/api/v1/uploads/${uploadId}/complete`,
      expect.objectContaining({ method: "POST" }),
    );
  });

  it("rejects unsupported input before requesting a signed URL", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch");
    render(<UploadWorkspace />);

    fireEvent.change(screen.getByLabelText("Choose image"), {
      target: { files: [new File(["not an image"], "notes.txt", { type: "text/plain" })] },
    });

    expect(screen.getByRole("alert")).toHaveTextContent("Choose a JPEG, PNG, or WebP image.");
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("keeps the selected image available after a retryable transfer failure", async () => {
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(
        jsonResponse({
          expiresAt: "2026-08-25T10:05:00Z",
          uploadId: "d463635f-fb4b-49bc-b0d1-e2e2f0183c76",
          uploadUrl: "http://storage.test/signed-upload",
        }),
      )
      .mockResolvedValueOnce(new Response(null, { status: 503 }));
    const user = userEvent.setup();
    render(<UploadWorkspace />);
    await user.upload(
      screen.getByLabelText("Choose image"),
      new File([new Uint8Array([1])], "retry.png", { type: "image/png" }),
    );

    await user.click(screen.getByRole("button", { name: "Upload solution" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("The image could not be uploaded.");
    expect(screen.getByRole("button", { name: "Retry upload" })).toBeEnabled();
    expect(screen.getByText("retry.png")).toBeInTheDocument();
  });
});
