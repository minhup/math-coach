import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiError, getCurrentUser, login, logout } from "./api";

afterEach(() => {
  vi.restoreAllMocks();
});

describe("API boundary", () => {
  it("validates a current-user response", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ displayName: "Internal learner", id: "user-1" })),
    );

    await expect(getCurrentUser()).resolves.toEqual({
      displayName: "Internal learner",
      id: "user-1",
    });
  });

  it("rejects a malformed success response", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ displayName: "Missing identifier" })),
    );

    await expect(getCurrentUser()).rejects.toMatchObject({
      code: "invalid_response",
      status: 502,
    });
  });

  it("preserves a stable API error", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(
        JSON.stringify({ error: { code: "invalid_invite", message: "That invite is not valid." } }),
        { status: 401 },
      ),
    );

    await expect(login("wrong-code")).rejects.toEqual(
      new ApiError("invalid_invite", "That invite is not valid.", 401),
    );
  });

  it("uses a safe fallback for a non-JSON upstream error", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response("not-json", { status: 502 }));

    await expect(getCurrentUser()).rejects.toMatchObject({
      code: "request_failed",
      message: "Something went wrong. Try again.",
      status: 502,
    });
  });

  it("accepts an empty successful logout response", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(new Response(null, { status: 204 }));

    await expect(logout()).resolves.toBeUndefined();
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/v1/auth/logout",
      expect.objectContaining({ credentials: "same-origin", method: "POST" }),
    );
  });
});
