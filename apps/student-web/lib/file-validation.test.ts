import { describe, expect, it } from "vitest";

import { formatFileSize, validateSolutionImage } from "./file-validation";

describe("validateSolutionImage", () => {
  it("accepts supported non-empty images within the limit", () => {
    const file = new File([new Uint8Array([1])], "solution.webp", { type: "image/webp" });
    expect(validateSolutionImage(file)).toBeNull();
  });

  it("rejects empty and oversized images", () => {
    expect(validateSolutionImage(new File([], "empty.png", { type: "image/png" }))).toMatch(
      "empty",
    );
    const oversized = new File([new Uint8Array(10 * 1024 * 1024 + 1)], "large.jpg", {
      type: "image/jpeg",
    });
    expect(validateSolutionImage(oversized)).toMatch("10 MB");
  });
});

describe("formatFileSize", () => {
  it("formats bytes, kilobytes, and megabytes", () => {
    expect(formatFileSize(42)).toBe("42 B");
    expect(formatFileSize(2048)).toBe("2 KB");
    expect(formatFileSize(2.5 * 1024 * 1024)).toBe("2.5 MB");
  });
});
