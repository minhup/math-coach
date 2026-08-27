import { expect, type Locator, type Page, test } from "@playwright/test";

const syntheticGeometryDescription =
  "A synthetic coordinate construction containing three free points and examples of every approved geometry primitive.";

interface ConstraintSnapshot {
  pointCoordinates: Record<string, [number, number]>;
  constraintErrors: Record<string, number>;
}

async function snapshot(output: Locator): Promise<ConstraintSnapshot> {
  return JSON.parse(await output.innerText()) as ConstraintSnapshot;
}

async function dragBy(page: Page, object: Locator, x: number, y: number): Promise<void> {
  await object.scrollIntoViewIfNeeded();
  const bounds = await object.boundingBox();
  if (!bounds) {
    throw new Error("Geometry object has no rendered bounds.");
  }
  const startX = bounds.x + bounds.width / 2;
  const startY = bounds.y + bounds.height / 2;
  await page.mouse.move(startX, startY);
  await page.mouse.down();
  await page.mouse.move(startX + x, startY + y, { steps: 8 });
  await page.mouse.up();
}

function geometryObject(page: Page, objectId: string): Locator {
  return page.locator(`[id$="_${objectId}"]`);
}

test("curated geometry preserves constraints and interactions on phone and tablet", async ({
  page,
}, testInfo) => {
  await page.goto("/");
  await page.getByLabel("Invite code").fill("MATH-COACH-LOCAL");
  await page.getByRole("button", { name: "Open workspace" }).click();
  await page.getByRole("link", { name: "Geometry spike" }).click();

  await expect(page.getByRole("heading", { name: "Interactive geometry engine" })).toBeVisible();
  await expect(
    page.getByText("Synthetic curated construction — not examination content"),
  ).toBeVisible();
  await expect(page.getByText("Interactive geometry ready.")).toBeAttached();

  const board = page.getByTestId("geometry-board");
  const constraintOutput = page.getByTestId("geometry-constraint-snapshot");
  await expect(board).toBeVisible();
  await expect(board).toHaveAttribute("role", "region");
  await expect(board).toHaveAttribute("aria-label", syntheticGeometryDescription);
  await expect(constraintOutput).toContainText("circumcircle:circumABC");
  await expect(board.locator("script, iframe, [onclick], [onload], [onerror]")).toHaveCount(0);

  const initial = await snapshot(constraintOutput);
  await page.reload();
  await expect(page.getByText("Interactive geometry ready.")).toBeAttached();
  await expect(page.getByTestId("geometry-constraint-snapshot")).toContainText(
    "circumcircle:circumABC",
  );
  expect(await snapshot(page.getByTestId("geometry-constraint-snapshot"))).toEqual(initial);

  const pointA = geometryObject(page, "A");
  const pointB = geometryObject(page, "B");
  const midpoint = geometryObject(page, "M");
  await expect(pointA).toBeVisible();
  await expect(pointB).toBeVisible();
  await expect(midpoint).toBeVisible();

  const beforeDrag = await snapshot(page.getByTestId("geometry-constraint-snapshot"));
  await dragBy(page, pointA, 32, -24);
  await expect
    .poll(
      async () =>
        (await snapshot(page.getByTestId("geometry-constraint-snapshot"))).pointCoordinates.A,
    )
    .not.toEqual(beforeDrag.pointCoordinates.A);
  const afterDrag = await snapshot(page.getByTestId("geometry-constraint-snapshot"));
  expect(afterDrag.pointCoordinates.B).toEqual(beforeDrag.pointCoordinates.B);
  expect(afterDrag.pointCoordinates.M).not.toEqual(beforeDrag.pointCoordinates.M);
  for (const error of Object.values(afterDrag.constraintErrors)) {
    expect(error).toBeLessThan(1e-7);
  }

  await dragBy(page, midpoint, 40, 30);
  await dragBy(page, pointB, -40, -30);
  await page.waitForTimeout(100);
  const afterLockedDrag = await snapshot(page.getByTestId("geometry-constraint-snapshot"));
  expect(afterLockedDrag.pointCoordinates.M).toEqual(afterDrag.pointCoordinates.M);
  expect(afterLockedDrag.pointCoordinates.B).toEqual(afterDrag.pointCoordinates.B);

  await pointB.tap();
  await expect(page.getByRole("status", { name: "Selection result" })).toHaveText("Selected B.");
  await pointA.click();
  await expect(page.getByRole("status", { name: "Selection result" })).toHaveText("Selected A.");

  await page.getByRole("button", { name: "Ask selection question" }).click();
  await expect(page.getByText("Select point A.")).toBeVisible();
  await expect(page.getByRole("button", { name: "Select C" })).toBeDisabled();
  await page.getByRole("button", { name: "Select B" }).click();
  await expect(page.getByRole("status", { name: "Selection result" })).toHaveText(
    "B is not the expected selection.",
  );
  await page.getByRole("button", { name: "Select A" }).focus();
  await page.keyboard.press("Enter");
  await expect(page.getByRole("status", { name: "Selection result" })).toHaveText(
    "A is the expected selection.",
  );

  await page.getByRole("button", { name: "Hide labelM" }).click();
  await expect(page.getByRole("status", { name: "Geometry action result" })).toHaveText(
    "Hide applied.",
  );
  await page.getByRole("button", { name: "Show labelM" }).click();
  await page.getByRole("button", { name: "Highlight A, B" }).click();
  await page.getByRole("button", { name: "Clear highlight" }).click();
  await page.getByRole("button", { name: "Focus triangle" }).click();
  await page.getByRole("button", { name: "Animate A" }).click();
  await expect(page.getByRole("status", { name: "Geometry action result" })).toHaveText(
    "Animation applied.",
  );

  await page.getByText("Static fallback", { exact: true }).click();
  await expect(
    page.getByRole("img", { name: `${syntheticGeometryDescription} Static fallback.` }),
  ).toHaveAttribute("src", "/fixtures/synthetic-m4-geometry-fallback.svg");

  const layoutReport = await page.evaluate(() => {
    const selectors = [
      ".geometry-spike-shell",
      ".geometry-layout",
      ".geometry-board",
      ".geometry-controls",
      ".geometry-action-list",
      ".geometry-selection-list",
      ".geometry-constraint-snapshot",
      ".geometry-static-fallback",
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
      path: `test-results/m4-geometry-${testInfo.project.name}.png`,
    });
  }
});
