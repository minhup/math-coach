import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { MathCoachApp } from "./math-coach-app";

function jsonResponse(payload: object, status = 200): Response {
  return new Response(JSON.stringify(payload), {
    headers: { "Content-Type": "application/json" },
    status,
  });
}

afterEach(() => {
  vi.restoreAllMocks();
});

describe("MathCoachApp", () => {
  it("moves from an unauthenticated check to invite login and the workspace", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(
        jsonResponse(
          { error: { code: "authentication_required", message: "Sign in again." } },
          401,
        ),
      )
      .mockResolvedValueOnce(
        jsonResponse({
          expiresAt: "2026-08-26T00:00:00Z",
          user: { displayName: "Internal learner", id: "5fc1ca89-a9aa-43dc-a87f-012d9be99ac0" },
        }),
      )
      .mockResolvedValueOnce(jsonResponse({ items: [] }))
      .mockResolvedValueOnce(
        jsonResponse({ error: { code: "profile_not_found", message: "Create a profile." } }, 404),
      );
    const user = userEvent.setup();

    render(<MathCoachApp />);

    expect(screen.getByText("Opening your workspace…")).toBeInTheDocument();
    const inviteInput = await screen.findByLabelText("Invite code");
    await user.type(inviteInput, "MATH-COACH-LOCAL");
    await user.click(screen.getByRole("button", { name: "Open workspace" }));

    expect(
      await screen.findByRole("heading", { name: "Create your study profile" }),
    ).toBeInTheDocument();
    expect(screen.getAllByText("Internal learner")).toHaveLength(2);
    expect(screen.getByRole("link", { name: "Correction spike" })).toHaveAttribute(
      "href",
      "/internal/math-correction",
    );
    expect(screen.getByRole("link", { name: "Geometry spike" })).toHaveAttribute(
      "href",
      "/internal/geometry-spike",
    );
    expect(fetchMock).toHaveBeenNthCalledWith(
      2,
      "/api/v1/auth/pilot-login",
      expect.objectContaining({ method: "POST" }),
    );
  });

  it("shows a safe invite error and allows another attempt", async () => {
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(
        jsonResponse(
          { error: { code: "authentication_required", message: "Sign in again." } },
          401,
        ),
      )
      .mockResolvedValueOnce(
        jsonResponse(
          { error: { code: "invalid_invite", message: "That invite is not valid." } },
          401,
        ),
      );
    const user = userEvent.setup();
    render(<MathCoachApp />);

    await user.type(await screen.findByLabelText("Invite code"), "WRONG-CODE");
    await user.click(screen.getByRole("button", { name: "Open workspace" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("That invite is not valid.");
    await waitFor(() =>
      expect(screen.getByRole("button", { name: "Open workspace" })).toBeEnabled(),
    );
  });

  it("shows a retryable state when the initial session check is unavailable", async () => {
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(
        jsonResponse(
          { error: { code: "storage_unavailable", message: "Temporarily unavailable." } },
          503,
        ),
      )
      .mockResolvedValueOnce(
        jsonResponse(
          { error: { code: "authentication_required", message: "Sign in again." } },
          401,
        ),
      );
    const user = userEvent.setup();
    render(<MathCoachApp />);

    expect(
      await screen.findByRole("heading", { name: "Your workspace could not open." }),
    ).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Retry connection" }));

    expect(await screen.findByLabelText("Invite code")).toBeInTheDocument();
  });

  it("keeps the workspace open and explains a failed sign-out", async () => {
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(jsonResponse({ displayName: "Internal learner", id: "user-1" }))
      .mockResolvedValueOnce(jsonResponse({ items: [] }))
      .mockResolvedValueOnce(
        jsonResponse({ error: { code: "profile_not_found", message: "Create a profile." } }, 404),
      )
      .mockResolvedValueOnce(
        jsonResponse(
          { error: { code: "service_unavailable", message: "Could not end the session." } },
          503,
        ),
      );
    const user = userEvent.setup();
    render(<MathCoachApp />);

    await screen.findByRole("heading", { name: "Create your study profile" });
    await user.click(await screen.findByRole("button", { name: "Sign out" }));

    expect(await screen.findByText("Could not end the session.")).toHaveAttribute("role", "alert");
    expect(screen.getByRole("heading", { name: "Create your study profile" })).toBeInTheDocument();
  });
});
