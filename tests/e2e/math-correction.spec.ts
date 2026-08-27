import { expect, test } from "@playwright/test";

const invalidFixtureSource = String.raw`\frac{PRIVATE_FIXTURE_SOURCE}{`;

test("internal learner corrects and confirms the synthetic typed transcript", async ({
  page,
}, testInfo) => {
  await page.goto("/");
  await page.getByLabel("Invite code").fill("MATH-COACH-LOCAL");
  await page.getByRole("button", { name: "Open workspace" }).click();
  await page.getByRole("link", { name: "Correction spike" }).click();

  await expect(page.getByRole("heading", { name: "Mathematical correction spike" })).toBeVisible();
  await expect(page.getByText("Synthetic fixture — not student work")).toBeVisible();

  const viewport = page.viewportSize();
  if (viewport === null) {
    throw new Error("The configured device project must provide a viewport.");
  }

  if (viewport.width < 768) {
    const photoTab = page.getByRole("tab", { name: "PHOTO" });
    const transcriptTab = page.getByRole("tab", { name: "TRANSCRIPT" });
    await expect(photoTab).toHaveAttribute("aria-selected", "true");
    await expect(
      page.getByRole("img", { name: "Original synthetic handwritten algebra solution" }),
    ).toBeVisible();
    await photoTab.focus();
    await photoTab.press("ArrowRight");
    await expect(transcriptTab).toBeFocused();
    await expect(transcriptTab).toHaveAttribute("aria-selected", "true");
    await transcriptTab.press("ArrowLeft");
    await expect(photoTab).toBeFocused();
    await transcriptTab.tap();
    await expect(page.getByRole("tabpanel", { name: "TRANSCRIPT" })).toBeVisible();
  } else {
    await expect(page.getByRole("region", { name: "Synthetic photo" })).toBeVisible();
    await expect(page.getByRole("region", { name: "Transcript correction" })).toBeVisible();
    await expect(
      page.getByRole("img", { name: "Original synthetic handwritten algebra solution" }),
    ).toBeVisible();
    await expect(page.getByRole("tab", { name: "PHOTO" })).toHaveCount(0);
  }

  await expect(page.locator(".math-renderer-inline .katex")).toBeVisible();
  await expect(page.locator(".math-renderer-display .katex").first()).toBeVisible();
  const correctionPlaceholder = page.getByRole("img", { name: "Math needs correction" });
  await expect(correctionPlaceholder).toBeVisible();
  const failedRenderer = page.locator(".math-renderer").filter({ has: correctionPlaceholder });
  await expect(failedRenderer.locator("a, img, iframe, script, [onload], [onerror]")).toHaveCount(
    0,
  );
  expect(await page.locator("body").evaluate((body) => body.innerHTML)).not.toContain(
    invalidFixtureSource,
  );

  const mathField = page.getByLabel("Edit mathematics in step 2, block 2");
  await expect(mathField).toBeVisible();
  await mathField.click();
  await mathField.press("ControlOrMeta+A");
  await mathField.pressSequentially("x^2=4");
  await expect(page.getByRole("img", { name: "Math needs correction" })).toHaveCount(0);

  const firstStep = page.getByRole("region", { name: "Step 1" });
  await firstStep.getByRole("button", { name: "Move block 1 down" }).click();
  await firstStep.getByRole("button", { name: "Split before block 2" }).click();
  await page.getByRole("button", { name: "Merge step 2 with previous" }).click();
  await page.getByRole("button", { name: "Move step 2 up" }).click();
  await page.getByRole("button", { name: "Confirm transcript for future grading" }).click();

  const snapshot = page.getByRole("status", { name: "Confirmed transcript snapshot" });
  await expect(snapshot).toContainText("Future authoritative grading input");
  await expect(snapshot.locator("li").first()).toContainText("synthetic-step-2: text → math");
  await expect(snapshot.locator("li").nth(1)).toContainText("synthetic-step-1: math → text");

  const layoutReport = await page.evaluate(() => {
    const selectors = [
      ".correction-shell",
      ".correction-panel",
      ".transcript-step",
      ".transcript-block",
      ".math-renderer",
      ".mathlive-editor",
      ".transcript-control-row",
    ];
    const viewportWidth = document.documentElement.clientWidth;
    const escaped = Array.from(document.querySelectorAll(selectors.join(",")))
      .map((element) => {
        const rect = element.getBoundingClientRect();
        return {
          className: element.className,
          left: rect.left,
          right: rect.right,
        };
      })
      .filter(({ left, right }) => left < -1 || right > viewportWidth + 1);
    return {
      documentClientWidth: viewportWidth,
      documentScrollWidth: document.documentElement.scrollWidth,
      escaped,
    };
  });
  expect(layoutReport.documentScrollWidth).toBeLessThanOrEqual(
    layoutReport.documentClientWidth + 1,
  );
  expect(layoutReport.escaped).toEqual([]);

  if (process.env.VISUAL_QA) {
    await page.screenshot({
      fullPage: true,
      path: `test-results/m3-correction-${testInfo.project.name}.png`,
    });
  }
});
