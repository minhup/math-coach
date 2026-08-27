import { expect, type Page, test } from "@playwright/test";

const syntheticPng = Buffer.from(
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=",
  "base64",
);

const inviteByProject: Record<string, string> = {
  "compact-chromium": "MATH-COACH-M5-COMPACT",
  "ipad-pro-11-landscape-webkit": "MATH-COACH-M5-IPAD-LANDSCAPE",
  "ipad-pro-11-portrait-webkit": "MATH-COACH-M5-IPAD-PORTRAIT",
  "iphone-13-webkit": "MATH-COACH-M5-IPHONE-13",
  "pixel-7-chromium": "MATH-COACH-M5-PIXEL-7",
};

async function placeCaret(page: Page, text: string, offset: number) {
  await page.getByRole("textbox", { name: "Editable transcript document" }).evaluate(
    (editor, input) => {
      const run = Array.from(
        editor.querySelectorAll<HTMLElement>("[data-transcript-text-id]"),
      ).find((element) => element.textContent?.includes(input.text));
      const node = run?.firstChild;
      if (node === undefined || node === null) {
        throw new Error(`Transcript text not found: ${input.text}`);
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

test("invited learner completes the deterministic multi-exam student journey", async ({
  page,
}, testInfo) => {
  await page.goto("/");

  await expect(page.getByRole("heading", { name: "Continue your practice." })).toBeVisible();
  const inviteCode = inviteByProject[testInfo.project.name];
  if (inviteCode === undefined) {
    throw new Error(`No synthetic invite is configured for ${testInfo.project.name}.`);
  }
  await page.getByLabel("Invite code").fill(inviteCode);
  await page.getByRole("button", { name: "Open workspace" }).click();

  const createProfileHeading = page.getByRole("heading", { name: "Create your study profile" });
  const existingProfileHeading = page.getByRole("heading", { name: "Your study profile" });
  await expect(createProfileHeading.or(existingProfileHeading)).toBeVisible();
  if (await createProfileHeading.isVisible()) {
    await page.getByRole("button", { name: "Create study profile" }).click();
    await expect(
      page.getByRole("heading", { name: "Add at least two active examination targets" }),
    ).toBeVisible();

    await page
      .getByRole("button", { name: "Add Synthetic Aurora Mathematics Examination" })
      .click();
    await expect(page.getByText("Synthetic Aurora Mathematics Examination")).toBeVisible();
    await expect(page.getByRole("button", { name: "Build today's combined plan" })).toHaveCount(0);
    await page
      .getByRole("button", { name: "Add Synthetic Harbor Mathematics Examination" })
      .click();
  }
  await expect(page.getByText("Synthetic Aurora Mathematics Examination")).toBeVisible();
  await expect(page.getByText("Synthetic Harbor Mathematics Examination")).toBeVisible();

  const buildPlan = page.getByRole("button", { name: "Build today's combined plan" });
  await buildPlan.focus();
  await buildPlan.press("Enter");
  await expect(page.getByRole("heading", { name: "Today's combined plan" })).toBeVisible();
  await expect(page.getByText("Supports 2 targets")).toBeVisible();
  await expect(page.getByText("Supports 1 target")).toBeVisible();
  await expect(page.getByText("SYN-M4-GEO-001", { exact: true })).toBeVisible();
  await expect(page.getByText("SYN-M2-GEO-001", { exact: true })).toBeVisible();

  await page.getByRole("button", { name: "Open SYN-M4-GEO-001" }).click();
  await expect(page.getByRole("heading", { name: "SYN-M4-GEO-001" })).toBeVisible();
  await expect(page.getByText("Pinned content version 1")).toBeVisible();
  await expect(page.getByLabel("Interactive geometry")).toBeVisible();
  await expect(page.getByText("Interactive geometry ready.")).toBeAttached();
  const selectPointA = page.getByRole("button", { name: "Select A" });
  await selectPointA.tap();
  await expect(page.getByRole("status", { name: "Selection result" })).toContainText("Selected A");

  await page.getByRole("button", { name: "Upload a synthetic solution" }).click();
  await page.getByLabel("Choose image").setInputFiles({
    buffer: syntheticPng,
    mimeType: "image/png",
    name: "synthetic-solution.png",
  });
  await page.getByRole("button", { name: "Upload solution" }).click();
  const uploadSuccess = page.getByText("Image received and verified");
  const uploadFailure = page.getByRole("alert").filter({
    hasText: "The image could not be uploaded.",
  });
  await expect(uploadSuccess.or(uploadFailure)).toBeVisible();
  if (await uploadFailure.isVisible()) {
    await page.getByRole("button", { name: "Retry upload" }).click();
  }
  await expect(uploadSuccess).toBeVisible();
  await page.getByRole("button", { name: "Use this upload" }).click();

  await expect(page.getByRole("heading", { name: "Review the transcript" })).toBeVisible();
  await placeCaret(page, "The synthetic draft", 19);
  await page.keyboard.type(" reviewed");
  await page.getByRole("button", { name: "Edit formula 1" }).click();
  const mathField = page.getByLabel("Edit formula 1");
  await expect(mathField).toBeFocused();
  await mathField.press("ControlOrMeta+A");
  await mathField.pressSequentially("M=(2,0)");
  await page.getByRole("button", { name: "Done editing formula 1" }).click();
  await expect(page.getByRole("textbox", { name: "Editable transcript document" })).toContainText(
    "draft reviewed",
  );
  await page.getByRole("button", { name: "Confirm transcript" }).click();

  await expect(page.getByRole("heading", { name: "Authoritative evaluation input" })).toBeVisible();
  await expect(page.getByLabel("Confirmed authoritative transcript")).toContainText(
    "draft reviewed",
  );
  await page.getByRole("button", { name: "Evaluate confirmed transcript" }).click();
  await expect(page.getByRole("heading", { name: "Deterministic feedback" })).toBeVisible();
  await expect(page.getByText(/Reference solutions are non-exhaustive/)).toBeVisible();
  await expect(page.locator(".math-render-failure")).toHaveCount(0);

  await page.getByRole("button", { name: "Request hint 1" }).click();
  await expect(page.getByText("Identify the free and constructed points.")).toBeVisible();
  await page.getByRole("button", { name: "Highlight A, B, C, M" }).click();
  await expect(page.getByRole("status", { name: "Geometry action result" })).toHaveText(
    "Highlight applied.",
  );
  await page.getByRole("button", { name: "Request hint 2" }).click();
  await expect(
    page.getByText("Use the midpoint definition before computing a distance."),
  ).toBeVisible();
  await page.getByRole("button", { name: "Ask selection question" }).click();
  await page.getByRole("button", { name: "Select A" }).click();
  await expect(page.getByRole("status", { name: "Selection result" })).toContainText(
    "A is the expected selection",
  );

  await page.getByRole("button", { name: "Retry this problem" }).click();
  await expect(page.getByRole("heading", { name: "New attempt ready" })).toBeVisible();
  await expect(page.getByText("Attempt 2 · same immutable content version 1")).toBeVisible();
  await page.getByRole("button", { name: "Study the linked concept" }).click();
  await expect(page.getByRole("heading", { name: "Midpoint coordinates" })).toBeVisible();
  await expect(page.getByLabel("Displayed mathematics")).toBeVisible();
  await page.getByRole("button", { name: "Complete session" }).click();

  await expect(page.getByRole("heading", { name: "Session complete" })).toBeVisible();
  await expect(page.getByText("2 active targets")).toBeVisible();
  await expect(page.getByText("2 attempts")).toBeVisible();
  await expect(page.getByText("Hints 1, 2")).toBeVisible();

  const layoutReport = await page.evaluate(() => {
    const viewportWidth = document.documentElement.clientWidth;
    const selectors = [
      ".app-shell",
      ".static-journey",
      ".journey-card",
      ".geometry-experience",
      ".transcript-editor",
      ".math-renderer",
    ];
    return {
      documentClientWidth: viewportWidth,
      documentScrollWidth: document.documentElement.scrollWidth,
      escaped: Array.from(document.querySelectorAll(selectors.join(",")))
        .map((element) => element.getBoundingClientRect())
        .filter(({ left, right }) => left < -1 || right > viewportWidth + 1).length,
    };
  });
  expect(layoutReport.documentScrollWidth).toBeLessThanOrEqual(
    layoutReport.documentClientWidth + 1,
  );
  expect(layoutReport.escaped).toBe(0);

  if (process.env.VISUAL_QA) {
    await page.screenshot({
      fullPage: true,
      path: `test-results/m5-static-journey-${testInfo.project.name}.png`,
    });
  }

  await page.reload();
  await expect(page.getByRole("heading", { name: "Your study profile" })).toBeVisible();
  await expect(page.getByText("Synthetic Aurora Mathematics Examination")).toBeVisible();
  await expect(page.getByText("Synthetic Harbor Mathematics Examination")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Session complete" })).toHaveCount(0);
  await page.getByRole("button", { name: "Sign out" }).click();
  await expect(page.getByRole("heading", { name: "Continue your practice." })).toBeVisible();
});
