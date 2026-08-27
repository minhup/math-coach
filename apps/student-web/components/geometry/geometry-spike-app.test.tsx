import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { GeometrySpikeApp } from "./geometry-spike-app";

const graph = vi.hoisted(() => {
  const create = vi.fn((type: string, parents: unknown[]) => {
    const coordinates = type === "point" ? (parents as number[]) : [0, 0];
    const element = {
      on: vi.fn(() => element),
      setAttribute: vi.fn(() => element),
      X: () => coordinates[0] ?? 0,
      Y: () => coordinates[1] ?? 0,
    };
    return element;
  });
  return {
    create,
    freeBoard: vi.fn(),
    initBoard: vi.fn(() => ({ create, update: vi.fn() })),
  };
});

vi.mock("jsxgraph", () => ({
  default: { JSXGraph: { initBoard: graph.initBoard, freeBoard: graph.freeBoard } },
}));

function jsonResponse(payload: object, status = 200): Response {
  return new Response(JSON.stringify(payload), {
    headers: { "Content-Type": "application/json" },
    status,
  });
}

afterEach(() => {
  vi.restoreAllMocks();
});

describe("GeometrySpikeApp", () => {
  it("authenticates before exposing the synthetic all-primitives fixture", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      jsonResponse({ displayName: "Internal learner", id: "user-synthetic" }),
    );
    render(<GeometrySpikeApp />);

    expect(screen.getByText("Checking geometry-spike access…")).toBeInTheDocument();
    expect(
      await screen.findByRole("heading", { name: "Interactive geometry engine" }),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Synthetic curated construction — not examination content"),
    ).toBeInTheDocument();
    expect(screen.getByLabelText("Interactive geometry")).toBeInTheDocument();
    expect(await screen.findByTestId("geometry-constraint-snapshot")).toBeInTheDocument();
  });

  it("does not expose the fixture without an authenticated session", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      jsonResponse({ error: { code: "authentication_required", message: "Sign in." } }, 401),
    );
    render(<GeometrySpikeApp />);

    expect(
      await screen.findByRole("heading", { name: "Authentication required" }),
    ).toBeInTheDocument();
    expect(screen.queryByLabelText("Interactive geometry")).toBeNull();
  });

  it("retries a temporary access failure", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockRejectedValueOnce(new Error("offline"))
      .mockResolvedValueOnce(
        jsonResponse({ displayName: "Internal learner", id: "user-synthetic" }),
      );
    render(<GeometrySpikeApp />);

    expect(
      await screen.findByRole("heading", { name: "Geometry spike unavailable" }),
    ).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Retry connection" }));

    expect(
      await screen.findByRole("heading", { name: "Interactive geometry engine" }),
    ).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });
});
