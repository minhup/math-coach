import { expect, test } from "@playwright/test";

const invalidFixtureSource = String.raw`\frac{PRIVATE_FIXTURE_SOURCE}{`;

test("internal learner corrects and confirms one flat simulated-OCR document", async ({
  page,
}, testInfo) => {
  await page.goto("/");
  await page.getByLabel("Invite code").fill("MATH-COACH-LOCAL");
  await page.getByRole("button", { name: "Open workspace" }).click();
  await page.getByRole("link", { name: "Correction spike" }).click();

  await expect(page.getByRole("heading", { name: "Mathematical correction spike" })).toBeVisible();
  await expect(
    page.getByText("Synthetic upload and simulated OCR — not student work"),
  ).toBeVisible();

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

  const document = page.getByRole("document", { name: "Editable transcript document" });
  await expect(document).toBeVisible();
  await expect(page.getByText("Simulated OCR transcript", { exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: /^Step \d/ })).toHaveCount(0);
  await expect(page.getByRole("button", { name: /split|merge|move step/i })).toHaveCount(0);
  await expect(document.locator("math-field")).toHaveCount(0);

  await expect(page.locator(".math-renderer-inline .katex")).toBeVisible();
  await expect(document.locator(".math-renderer-display .katex").first()).toBeVisible();
  const correctionPlaceholder = page.getByRole("img", { name: "Math needs correction" });
  await expect(correctionPlaceholder).toBeVisible();
  const failedRenderer = page.locator(".math-renderer").filter({ has: correctionPlaceholder });
  await expect(failedRenderer.locator("a, img, iframe, script, [onload], [onerror]")).toHaveCount(
    0,
  );
  expect(await page.locator("body").evaluate((body) => body.innerHTML)).not.toContain(
    invalidFixtureSource,
  );

  await page.getByLabel("Edit formula 4").click();
  const mathField = page.getByLabel("Edit mathematics block 4");
  await expect(mathField).toBeVisible();
  await expect(correctionPlaceholder).toHaveCount(0);
  await mathField.click();
  await mathField.press("ControlOrMeta+A");
  await mathField.pressSequentially("x^2=4");
  await page.getByLabel("Done editing formula 4").click();
  await expect(document.locator("math-field")).toHaveCount(0);
  await expect(page.getByRole("img", { name: "Math needs correction" })).toHaveCount(0);

  const firstText = page.getByLabel("Edit text block 1");
  await firstText.fill("Factor the quadratic expression carefully:");
  await page.getByLabel("Block 1 options").click();
  await page.getByRole("button", { name: "Move block 1 down" }).click();
  await expect(page.getByLabel("Edit text block 2")).toHaveValue(
    "Factor the quadratic expression carefully:",
  );
  await page.getByLabel("Block 2 options").click();

  await page.getByRole("button", { name: "Add text block" }).click();
  await page.getByLabel("Edit text block 7").fill("Temporary OCR line");
  await page.getByLabel("Block 7 options").click();
  await page.getByRole("button", { name: "Delete block 7" }).click();
  await expect(page.getByLabel("Edit text block 7")).toHaveCount(0);

  await page.getByLabel("Confirm transcript").click();
  const confirmation = page.getByRole("status", { name: "Confirmed transcript" });
  await expect(confirmation).toContainText("Future authoritative grading input");
  const confirmedContent = confirmation.locator(".transcript-confirmed-document > *");
  await expect(confirmedContent).toHaveCount(6);
  await expect(confirmedContent.first()).toHaveClass(/math-renderer/);
  await expect(confirmedContent.nth(1)).toHaveText("Factor the quadratic expression carefully:");
  const confirmationMarkup = await confirmation.evaluate((element) => element.innerHTML);
  expect(confirmationMarkup).not.toMatch(/synthetic-(?:text|math)|schemaVersion|stepId|→/);

  const bodyMarkup = await page.locator("body").evaluate((body) => body.innerHTML);
  expect(bodyMarkup).not.toContain(invalidFixtureSource);
  expect(bodyMarkup).not.toMatch(/synthetic-step|stepId/);

  const layoutReport = await page.evaluate(() => {
    const selectors = [
      ".correction-shell",
      ".correction-panel",
      ".transcript-document",
      ".transcript-block",
      ".transcript-block-menu",
      ".math-renderer",
      ".mathlive-editor",
      ".transcript-control-row",
      ".transcript-confirmed-document",
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
