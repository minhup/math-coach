import { expect, type Page, test } from "@playwright/test";

const invalidFixtureSource = String.raw`\frac{PRIVATE_FIXTURE_SOURCE}{`;

async function placeCaret(page: Page, text: string, offset: number) {
  await page.getByRole("textbox", { name: "Editable transcript document" }).evaluate(
    (editor, input) => {
      const walker = document.createTreeWalker(editor, NodeFilter.SHOW_TEXT);
      let node = walker.nextNode();
      while (node !== null && !node.textContent?.includes(input.text)) {
        node = walker.nextNode();
      }
      if (node === null) {
        throw new Error(`Text node not found: ${input.text}`);
      }
      const range = document.createRange();
      range.setStart(node, input.offset);
      range.collapse(true);
      const selection = window.getSelection();
      selection?.removeAllRanges();
      selection?.addRange(range);
      (editor as HTMLElement).focus();
      editor.dispatchEvent(new PointerEvent("pointerup", { bubbles: true }));
    },
    { offset, text },
  );
}

test("internal learner edits one inline simulated-OCR document", async ({ page }, testInfo) => {
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

  const editor = page.getByRole("textbox", { name: "Editable transcript document" });
  await expect(editor).toBeVisible();
  await expect(editor).toHaveAttribute("contenteditable", "plaintext-only");
  await expect(page.getByText("Simulated OCR transcript", { exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: /^Step \d/ })).toHaveCount(0);
  await expect(page.getByRole("button", { name: /split|merge|move step|add text/i })).toHaveCount(
    0,
  );
  await expect(editor.locator("textarea, .transcript-block, math-field")).toHaveCount(0);

  await expect(page.locator(".math-renderer-inline .katex").first()).toBeVisible();
  const correctionPlaceholder = page.getByRole("img", { name: "Math needs correction" });
  await expect(correctionPlaceholder).toBeVisible();
  const failedRenderer = page.locator(".math-renderer").filter({ has: correctionPlaceholder });
  await expect(failedRenderer.locator("a, img, iframe, script, [onload], [onerror]")).toHaveCount(
    0,
  );
  expect(await page.locator("body").evaluate((body) => body.innerHTML)).not.toContain(
    invalidFixtureSource,
  );

  await page.getByRole("button", { name: "Edit formula 2" }).click();
  const invalidMathField = page.getByLabel("Edit formula 2");
  await expect(invalidMathField).toBeFocused();
  await expect(correctionPlaceholder).toHaveCount(0);
  await invalidMathField.press("ControlOrMeta+A");
  await invalidMathField.pressSequentially("x^2=4");
  await page.getByRole("button", { name: "Done editing formula 2" }).click();
  await expect(page.getByRole("img", { name: "Math needs correction" })).toHaveCount(0);

  await placeCaret(page, "Factor the quadratic expression", 6);
  await page.keyboard.type(" carefully");
  await page.getByRole("button", { name: "Insert formula at caret" }).click();
  const insertedMathField = page.getByLabel("Edit formula 1");
  await expect(insertedMathField).toBeFocused();
  await expect
    .poll(() =>
      insertedMathField.evaluate((field) => Reflect.get(field, "mathVirtualKeyboardPolicy")),
    )
    .toBe("auto");
  if (process.env.VISUAL_QA) {
    await page.screenshot({
      fullPage: true,
      path: `test-results/m3-correction-edit-${testInfo.project.name}.png`,
    });
  }
  await insertedMathField.pressSequentially("y=1");
  await page.getByRole("button", { name: "Done editing formula 1" }).click();
  await expect(editor.locator("math-field")).toHaveCount(0);
  await expect(editor).toContainText("Factor carefully");

  await placeCaret(page, ".\nSet each factor equal to zero", 0);
  await page.keyboard.press("Backspace");
  let dialog = page.getByRole("alertdialog", { name: "Delete this formula?" });
  await expect(dialog).toBeVisible();
  await expect(editor.locator("[data-transcript-math-id]")).toHaveCount(4);
  if (process.env.VISUAL_QA) {
    await page.screenshot({
      fullPage: true,
      path: `test-results/m3-correction-delete-${testInfo.project.name}.png`,
    });
  }
  await expect(dialog.getByRole("button", { name: "Keep formula" })).toBeFocused();
  await page.keyboard.press("Escape");
  await expect(dialog).toHaveCount(0);
  await expect(editor.locator("[data-transcript-math-id]")).toHaveCount(4);

  await placeCaret(page, ".\nSet each factor equal to zero", 0);
  await page.keyboard.press("Backspace");
  dialog = page.getByRole("alertdialog", { name: "Delete this formula?" });
  await dialog.getByRole("button", { name: "Delete formula" }).click();
  await expect(editor.locator("[data-transcript-math-id]")).toHaveCount(3);

  await page.getByRole("button", { name: "Edit formula 3" }).click();
  await page.getByRole("button", { name: "Move formula 3 earlier" }).click();
  await page.getByRole("button", { name: "Done editing formula 3" }).click();

  await page.getByRole("button", { name: "Confirm transcript" }).click();
  const confirmation = page.getByRole("status", { name: "Confirmed transcript" });
  await expect(confirmation).toContainText("Future authoritative grading input");
  const confirmedContent = confirmation.locator(".transcript-confirmed-document > *");
  await expect(confirmedContent).toHaveCount(7);
  await expect(confirmedContent.first()).toHaveText("Factor carefully");
  await expect(confirmedContent.nth(1)).toHaveClass(/math-renderer-inline/);
  await expect(confirmedContent.nth(2)).toContainText("the quadratic expression");
  const confirmationMarkup = await confirmation.evaluate((element) => element.innerHTML);
  expect(confirmationMarkup).not.toMatch(/synthetic-(?:text|math)|schemaVersion|stepId|→/);

  const bodyMarkup = await page.locator("body").evaluate((body) => body.innerHTML);
  expect(bodyMarkup).not.toContain(invalidFixtureSource);
  expect(bodyMarkup).not.toMatch(/synthetic-step|stepId/);

  const layoutReport = await page.evaluate(() => {
    const selectors = [
      ".correction-shell",
      ".correction-panel",
      ".transcript-toolbar",
      ".transcript-document",
      ".transcript-math-token",
      ".math-renderer",
      ".mathlive-editor",
      ".transcript-formula-actions",
      ".transcript-confirmed-document",
    ];
    const viewportWidth = document.documentElement.clientWidth;
    const escaped = Array.from(document.querySelectorAll(selectors.join(",")))
      .map((element) => {
        const rect = element.getBoundingClientRect();
        return { className: element.className, left: rect.left, right: rect.right };
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
