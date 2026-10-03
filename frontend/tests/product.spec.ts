import { test, expect, type Page } from "@playwright/test";
async function login(page: Page) {
  await page.goto("/");
  await page
    .getByLabel("Email address")
    .fill(process.env.ADMIN_EMAIL ?? "jayden@example.com");
  await page
    .getByLabel("Password", { exact: true })
    .fill(process.env.ADMIN_PASSWORD ?? "Local-demo-pass-2026");
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Good code needs evidence." }),
  ).toBeVisible();
}
async function run(page: Page, name: string, agent: string) {
  await page
    .getByRole("button", { name: "New evaluation", exact: true })
    .click();
  const dialog = page.getByRole("dialog");
  await dialog.getByLabel("Evaluation name").fill(name);
  await dialog
    .getByRole("combobox", { name: "Agent", exact: true })
    .selectOption(agent);
  await dialog.getByRole("button", { name: "Start evaluation" }).click();
  await expect(page.getByRole("heading", { name, exact: true })).toBeVisible();
  await expect(
    page.locator(".run-banner").getByText("Completed", { exact: true }),
  ).toBeVisible({ timeout: 40000 });
}
test("evaluate both baselines, inspect actual failures, export and compare", async ({
  page,
}) => {
  await login(page);
  await run(page, "Reference control", "reference");
  await expect(page.getByText("100.0%", { exact: true })).toBeVisible();
  await page
    .getByRole("button", { name: "Inspect", exact: true })
    .first()
    .click();
  await expect(
    page.getByRole("dialog").getByText("Case 1", { exact: true }),
  ).toBeVisible();
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Source code" })
    .click();
  await expect(page.locator(".source")).toContainText("def solve");
  await page.getByRole("button", { name: "Close dialog" }).click();
  const jsonHref = await page
    .getByRole("link", { name: "JSON report" })
    .getAttribute("href");
  const exportResponse = await page.request.get(jsonHref!);
  expect(exportResponse.ok()).toBeTruthy();
  expect((await exportResponse.json()).score).toBe(100);
  await page.getByRole("button", { name: "All evaluations" }).click();
  await run(page, "Naive control", "naive");
  await expect(page.getByText("100.0%", { exact: true })).not.toBeVisible();
  await page
    .getByRole("button", { name: "Inspect", exact: true })
    .first()
    .click();
  await expect(
    page.getByRole("dialog").getByText("Failed", { exact: true }).first(),
  ).toBeVisible();
  await page.getByRole("button", { name: "Close dialog" }).click();
  await page.getByRole("button", { name: "Compare runs", exact: true }).click();
  await page
    .getByRole("combobox", { name: "Left evaluation", exact: true })
    .selectOption({ label: "Reference control" });
  await page
    .getByRole("combobox", { name: "Right evaluation", exact: true })
    .selectOption({ label: "Naive control" });
  await page.getByRole("button", { name: "Compare", exact: true }).click();
  await expect(page.locator(".comparison")).toHaveCount(2);
  await expect(page.locator(".comparison").first()).toContainText("100.0%");
  await page.getByRole("button", { name: "Sign out" }).click();
  await expect(
    page.getByRole("heading", { name: "Open your workspace" }),
  ).toBeVisible();
});
test("task library and mobile navigation are usable without page overflow", async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await login(page);
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBeTruthy();
  await page.getByRole("button", { name: "Open navigation" }).click();
  await page.getByRole("button", { name: "Task library", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Know what you are measuring." }),
  ).toBeVisible();
  await page.getByRole("button", { name: "View task" }).first().click();
  await expect(page.getByRole("dialog")).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog")).not.toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBeTruthy();
  await page.getByRole("button", { name: "Open navigation" }).click();
  await page.getByRole("button", { name: "Environment", exact: true }).click();
  await expect(
    page.getByText(
      "Demo mode executes only the exact authored baseline fixtures. External model source is refused.",
    ),
  ).toBeVisible();
});
test("mismatched task subsets cannot produce a misleading comparison", async ({
  page,
}) => {
  await login(page);
  await run(page, "Compatibility control", "reference");
  await page.getByRole("button", { name: "All evaluations" }).click();
  await page
    .getByRole("button", { name: "New evaluation", exact: true })
    .click();
  const dialog = page.getByRole("dialog");
  await dialog.getByLabel("Evaluation name").fill("Subset control");
  const boxes = dialog.getByRole("checkbox");
  for (let i = 1; i < 6; i++) await boxes.nth(i).uncheck();
  await dialog.getByRole("button", { name: "Start evaluation" }).click();
  await expect(
    page.locator(".run-banner").getByText("Completed", { exact: true }),
  ).toBeVisible({ timeout: 40000 });
  await page.getByRole("button", { name: "Compare runs", exact: true }).click();
  await page
    .getByRole("combobox", { name: "Left evaluation", exact: true })
    .selectOption({ label: "Compatibility control" });
  await page
    .getByRole("combobox", { name: "Right evaluation", exact: true })
    .selectOption({ label: "Subset control" });
  await page.getByRole("button", { name: "Compare", exact: true }).click();
  await expect(page.getByRole("alert")).toContainText("same suite fingerprint");
  await expect(page.locator(".comparison")).toHaveCount(0);
});
