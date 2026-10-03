import { chromium } from "@playwright/test";
import fs from "node:fs";
const browser = await chromium.launch(
  process.env.CHROMIUM_PATH
    ? { executablePath: process.env.CHROMIUM_PATH, args: ["--no-sandbox"] }
    : {},
);
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
const errors = [];
page.on("pageerror", (e) => errors.push(e.message));
await page.goto("http://127.0.0.1:8100");
await page
  .getByLabel("Email address")
  .fill(process.env.ADMIN_EMAIL ?? "jayden@example.com");
await page
  .getByLabel("Password", { exact: true })
  .fill(process.env.ADMIN_PASSWORD ?? "Local-demo-pass-2026");
await page.getByRole("button", { name: "Sign in", exact: true }).click();
await page
  .getByRole("heading", { name: "Good code needs evidence." })
  .waitFor();
await page
  .getByRole("button", { name: "Reference control", exact: true })
  .waitFor();
fs.mkdirSync("../docs/screenshots", { recursive: true });
await page.screenshot({
  path: "../docs/screenshots/workspace.png",
  fullPage: true,
});
await page
  .getByRole("button", { name: "Reference control", exact: true })
  .click();
await page
  .getByRole("heading", { name: "Reference control", exact: true })
  .waitFor();
await page.getByText("100.0%", { exact: true }).waitFor();
await page.screenshot({
  path: "../docs/screenshots/evaluation.png",
  fullPage: true,
});
await page.getByRole("button", { name: "Compare runs", exact: true }).click();
await page
  .getByRole("combobox", { name: "Left evaluation", exact: true })
  .selectOption({ label: "Reference control" });
await page
  .getByRole("combobox", { name: "Right evaluation", exact: true })
  .selectOption({ label: "Naive control" });
await page.getByRole("button", { name: "Compare", exact: true }).click();
await page.locator(".comparison").first().waitFor();
await page.screenshot({
  path: "../docs/screenshots/comparison.png",
  fullPage: true,
});
await page.getByRole("button", { name: "Task library", exact: true }).click();
await page
  .getByRole("heading", { name: "Know what you are measuring." })
  .waitFor();
await page.screenshot({
  path: "../docs/screenshots/task-library.png",
  fullPage: true,
});
await page.setViewportSize({ width: 390, height: 844 });
await page.screenshot({
  path: "../docs/screenshots/mobile-library.png",
  fullPage: true,
});
await browser.close();
if (errors.length) throw new Error(errors.join("\n"));
console.log("Screenshots captured; no browser runtime errors.");
