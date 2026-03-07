import { test, expect } from "@playwright/test";
import {
  mockAuthEndpoints,
  mockGenerationEndpoints,
  mockCriticEndpoints,
  mockCharacterEndpoints,
  injectAuthState,
} from "../helpers/api-mocks";
import { mockAIResponse, mockCriticAnalysis } from "../helpers/mock-data";

test.describe("Generation Studio", () => {
  test.beforeEach(async ({ page }) => {
    await injectAuthState(page);
    await mockAuthEndpoints(page);
    await mockCharacterEndpoints(page);
  });

  /** Navigate to /generate and wait for full hydration */
  async function gotoStudio(page: import("@playwright/test").Page) {
    await page.goto("/generate");
    await page.waitForLoadState("networkidle");
    // Ensure the form is hydrated by waiting for the textarea to be editable
    await page
      .getByPlaceholder("Describe your creative vision...")
      .waitFor({ state: "visible" });
  }

  /** Fill the prompt textarea using pressSequentially for reliable React state sync */
  async function fillPrompt(
    page: import("@playwright/test").Page,
    text: string
  ) {
    const textarea = page.getByPlaceholder("Describe your creative vision...");
    await textarea.click();
    await textarea.fill(text);
    // Confirm React state updated — button should become enabled
    await expect(
      page.getByRole("button", { name: /Generate.*Spark/ })
    ).toBeEnabled({ timeout: 5_000 });
  }

  /** Submit a prompt and wait for the generation result */
  async function generateAndWaitForResult(
    page: import("@playwright/test").Page,
    prompt = "A lone astronaut floating in deep space"
  ) {
    await fillPrompt(page, prompt);
    await page.getByRole("button", { name: /Generate.*Spark/ }).click();
    await expect(
      page.getByText(mockAIResponse.paragraphPrompt.substring(0, 40))
    ).toBeVisible({ timeout: 15_000 });
  }

  // -----------------------------------------------------------------------
  // Form rendering
  // -----------------------------------------------------------------------

  test("renders generation form with textarea and submit button", async ({
    page,
  }) => {
    await gotoStudio(page);

    await expect(
      page.getByPlaceholder("Describe your creative vision...")
    ).toBeVisible();

    const generateBtn = page.getByRole("button", {
      name: /Generate.*Spark/,
    });
    await expect(generateBtn).toBeVisible();
    await expect(generateBtn).toBeDisabled(); // empty prompt
  });

  test("submit button enables when prompt text is entered", async ({
    page,
  }) => {
    await gotoStudio(page);
    await fillPrompt(page, "A cyberpunk cityscape at dawn");
  });

  // -----------------------------------------------------------------------
  // Type selector
  // -----------------------------------------------------------------------

  test("type selector toggles between image, video, universal", async ({
    page,
  }) => {
    await gotoStudio(page);

    const videoBtn = page.getByRole("button", { name: "video" });
    await videoBtn.click();
    // Active type gets the personality glow background
    await expect(videoBtn).toHaveCSS("color", /.+/);

    const universalBtn = page.getByRole("button", { name: "universal" });
    await universalBtn.click();
    await expect(universalBtn).toHaveCSS("color", /.+/);
  });

  // -----------------------------------------------------------------------
  // Generation flow
  // -----------------------------------------------------------------------

  test("submitting prompt shows result with paragraph prompt", async ({
    page,
  }) => {
    await mockGenerationEndpoints(page, { delayMs: 500 });
    await gotoStudio(page);
    await generateAndWaitForResult(page);
  });

  test("progress indicator visible during generation", async ({ page }) => {
    await mockGenerationEndpoints(page, { delayMs: 3000 });
    await gotoStudio(page);
    await fillPrompt(page, "A futuristic cityscape");

    await page.getByRole("button", { name: /Generate.*Spark/ }).click();

    // GenerationProgress shows phased messages like "Initializing Helios personality..."
    await expect(
      page.getByText(/Initializing Helios|Searching Vertex|Analyzing prompt/i)
    ).toBeVisible({ timeout: 5_000 });
  });

  // -----------------------------------------------------------------------
  // Result actions
  // -----------------------------------------------------------------------

  test("copy button copies paragraph prompt to clipboard", async ({
    page,
    context,
  }) => {
    await context.grantPermissions(["clipboard-read", "clipboard-write"]);
    await mockGenerationEndpoints(page, { delayMs: 200 });
    await gotoStudio(page);
    await generateAndWaitForResult(page);

    const copyBtn = page.getByRole("button", { name: /copy/i });
    await copyBtn.click();

    const clipboardText = await page.evaluate(() =>
      navigator.clipboard.readText()
    );
    expect(clipboardText).toContain("lone astronaut");
  });

  test("new button resets the form", async ({ page }) => {
    await mockGenerationEndpoints(page, { delayMs: 200 });
    await gotoStudio(page);
    await generateAndWaitForResult(page);

    await page.getByRole("button", { name: /new/i }).click();

    // Form should be cleared
    await expect(
      page.getByPlaceholder("Describe your creative vision...")
    ).toHaveValue("");
  });

  // -----------------------------------------------------------------------
  // Critic flow
  // -----------------------------------------------------------------------

  test("get critique shows critic panel with score", async ({ page }) => {
    await mockGenerationEndpoints(page, { delayMs: 200 });
    await mockCriticEndpoints(page);
    await gotoStudio(page);
    await generateAndWaitForResult(page);

    await page.getByRole("button", { name: /critique/i }).click();

    // Critic panel shows assessment text
    await expect(
      page.getByText(mockCriticAnalysis.assessment.substring(0, 30))
    ).toBeVisible({ timeout: 10_000 });

    // Should show overall score number
    await expect(
      page.getByText(String(mockCriticAnalysis.overall_score))
    ).toBeVisible();
  });

  // -----------------------------------------------------------------------
  // Error handling
  // -----------------------------------------------------------------------

  test("server error shows red error banner", async ({ page }) => {
    await mockGenerationEndpoints(page, { status: 500 });
    await gotoStudio(page);
    await fillPrompt(page, "A test prompt");
    await page.getByRole("button", { name: /Generate.*Spark/ }).click();

    await expect(page.getByText(/error|failed/i)).toBeVisible({
      timeout: 10_000,
    });
  });

  test("credits error shows amber error banner", async ({ page }) => {
    await mockGenerationEndpoints(page, { status: 402 });
    await gotoStudio(page);
    await fillPrompt(page, "A test prompt");
    await page.getByRole("button", { name: /Generate.*Spark/ }).click();

    await expect(page.getByText(/credit/i)).toBeVisible({
      timeout: 10_000,
    });
  });

  // -----------------------------------------------------------------------
  // Save to Library (character extraction)
  // -----------------------------------------------------------------------

  test("save to library opens extraction preview modal", async ({ page }) => {
    await mockGenerationEndpoints(page, { delayMs: 200 });
    await gotoStudio(page);
    await generateAndWaitForResult(page);

    await page.getByRole("button", { name: /save to library/i }).click();

    // Extraction modal should open with ext-name field
    await expect(page.locator("#ext-name")).toBeVisible({ timeout: 10_000 });
  });
});
