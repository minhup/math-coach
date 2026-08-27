import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { CorrectionSpikeApp } from "./correction-spike-app";

vi.mock("mathlive", () => ({}));

function jsonResponse(payload: object, status = 200): Response {
  return new Response(JSON.stringify(payload), {
    headers: { "Content-Type": "application/json" },
    status,
  });
}

function mockViewport(tablet: boolean) {
  Object.defineProperty(window, "matchMedia", {
    configurable: true,
    value: vi.fn().mockReturnValue({
      addEventListener: vi.fn(),
      matches: tablet,
      removeEventListener: vi.fn(),
    }),
  });
}

afterEach(() => {
  vi.restoreAllMocks();
  Reflect.deleteProperty(window, "matchMedia");
});

describe("CorrectionSpikeApp", () => {
  it("checks authentication and exposes synthetic phone photo/transcript tabs", async () => {
    mockViewport(false);
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      jsonResponse({ displayName: "Internal learner", id: "user-synthetic" }),
    );
    const user = userEvent.setup();
    const { container } = render(<CorrectionSpikeApp />);

    expect(screen.getByText("Checking correction-spike access…")).toBeInTheDocument();
    expect(
      await screen.findByRole("heading", { name: "Mathematical correction spike" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Synthetic fixture — not student work")).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "PHOTO" })).toHaveAttribute("aria-selected", "true");
    expect(screen.queryByRole("tabpanel", { name: "TRANSCRIPT" })).toBeNull();

    await user.click(screen.getByRole("tab", { name: "TRANSCRIPT" }));
    expect(screen.getByRole("tabpanel", { name: "TRANSCRIPT" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "TRANSCRIPT" })).toHaveAttribute(
      "aria-selected",
      "true",
    );
    expect(container.innerHTML).not.toContain("PRIVATE_FIXTURE_SOURCE");
  });

  it("shows both synthetic panels without tabs on tablet layouts", async () => {
    mockViewport(true);
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      jsonResponse({ displayName: "Internal learner", id: "user-synthetic" }),
    );

    render(<CorrectionSpikeApp />);

    expect(await screen.findByRole("region", { name: "Synthetic photo" })).toBeInTheDocument();
    expect(screen.getByRole("region", { name: "Transcript correction" })).toBeInTheDocument();
    expect(screen.queryByRole("tab", { name: "PHOTO" })).toBeNull();
  });

  it("shows an authentication-required state without exposing fixtures", async () => {
    mockViewport(false);
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      jsonResponse({ error: { code: "authentication_required", message: "Sign in again." } }, 401),
    );

    render(<CorrectionSpikeApp />);

    expect(
      await screen.findByRole("heading", { name: "Authentication required" }),
    ).toBeInTheDocument();
    expect(screen.queryByText("Synthetic fixture — not student work")).toBeNull();
  });

  it("retries a temporary session failure", async () => {
    mockViewport(false);
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockRejectedValueOnce(new Error("offline"))
      .mockResolvedValueOnce(
        jsonResponse({ displayName: "Internal learner", id: "user-synthetic" }),
      );
    const user = userEvent.setup();

    render(<CorrectionSpikeApp />);

    expect(
      await screen.findByRole("heading", { name: "Correction spike unavailable" }),
    ).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Retry connection" }));

    expect(
      await screen.findByRole("heading", { name: "Mathematical correction spike" }),
    ).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });
});
