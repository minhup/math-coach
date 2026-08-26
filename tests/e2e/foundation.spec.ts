import { expect, test } from "@playwright/test";

const syntheticPng = Buffer.from(
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=",
  "base64",
);

test("internal learner signs in and completes a synthetic image upload", async ({
  page,
}, testInfo) => {
  await page.goto("/");

  await expect(page.getByRole("heading", { name: "Continue your practice." })).toBeVisible();
  await page.getByLabel("Invite code").fill("MATH-COACH-LOCAL");
  await page.getByRole("button", { name: "Open workspace" }).click();

  await expect(page.getByRole("heading", { name: "From paper to useful feedback." })).toBeVisible();
  await expect(page.getByText("Visual correction arrives in Milestone 3")).toBeVisible();
  await page.getByLabel("Choose image").setInputFiles({
    buffer: syntheticPng,
    mimeType: "image/png",
    name: "synthetic-solution.png",
  });
  await expect(page.getByAltText("Preview of the selected paper solution")).toBeVisible();
  await expect(page.getByText("synthetic-solution.png")).toBeVisible();

  const uploadButton = page.getByRole("button", { name: "Upload solution" });
  await uploadButton.scrollIntoViewIfNeeded();
  await expect(uploadButton).toBeEnabled();
  await uploadButton.click();
  await expect(page.getByText("Image received and verified")).toBeVisible();

  await page.getByRole("link", { name: "Content preview" }).click();
  await expect(page.getByRole("heading", { name: "SYN-M2-GEO-001" })).toBeVisible();
  await expect(page.getByText("SYN-AURORA-2027")).toBeVisible();
  await expect(page.getByText("SYN-HARBOR-2027")).toBeVisible();
  await expect(page.getByText("Reference solutions are non-exhaustive.")).toBeVisible();
  await expect(page.getByText(/A coordinate triangle with A at zero/)).toBeVisible();

  const horizontalOverflow = await page.evaluate(
    () => document.documentElement.scrollWidth > document.documentElement.clientWidth + 1,
  );
  expect(horizontalOverflow).toBe(false);

  if (process.env.VISUAL_QA) {
    await page.screenshot({
      fullPage: true,
      path: `test-results/visual-${testInfo.project.name}.png`,
    });
  }

  await page.getByRole("link", { name: "Back to workspace" }).click();
  const signOut = page.getByRole("button", { name: "Sign out" });
  await signOut.scrollIntoViewIfNeeded();
  await expect(signOut).toBeEnabled();
  await signOut.click();
  await expect(page.getByRole("heading", { name: "Continue your practice." })).toBeVisible();
});
