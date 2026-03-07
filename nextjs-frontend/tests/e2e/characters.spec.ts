import { test, expect } from "@playwright/test";
import {
  mockAuthEndpoints,
  mockCharacterEndpoints,
  injectAuthState,
} from "../helpers/api-mocks";
import { mockCharacter } from "../helpers/mock-data";

test.describe("Character Management", () => {
  test.beforeEach(async ({ page }) => {
    await injectAuthState(page);
    await mockAuthEndpoints(page);
  });

  /** Helper: select entity type from Radix Select dropdown with retry */
  async function selectEntityType(
    page: import("@playwright/test").Page,
    entityType: string
  ) {
    const trigger = page.getByRole("combobox").first();
    const option = page.locator(`[role="option"]`).filter({ hasText: entityType });

    // Radix Select portal can be flaky — retry the trigger click if options don't appear
    for (let attempt = 0; attempt < 3; attempt++) {
      await trigger.click();
      try {
        await option.waitFor({ state: "visible", timeout: 3_000 });
        await option.click();
        return;
      } catch {
        // Close the potentially stuck dropdown by pressing Escape, then retry
        await page.keyboard.press("Escape");
      }
    }
    // Final attempt — fail loudly
    await trigger.click();
    await option.waitFor({ state: "visible", timeout: 5_000 });
    await option.click();
  }

  // -----------------------------------------------------------------------
  // Character library page
  // -----------------------------------------------------------------------

  test("renders character library with character cards", async ({ page }) => {
    await mockCharacterEndpoints(page);
    await page.goto("/characters");
    await page.waitForLoadState("networkidle");

    await expect(
      page.getByRole("heading", { name: "Characters" })
    ).toBeVisible();

    await expect(page.getByText(mockCharacter.name)).toBeVisible({
      timeout: 10_000,
    });
  });

  test("empty library shows empty state with create CTA", async ({ page }) => {
    await mockCharacterEndpoints(page, { emptyList: true });
    await page.goto("/characters");
    await page.waitForLoadState("networkidle");

    await expect(page.getByText("No characters yet")).toBeVisible({
      timeout: 10_000,
    });
    await expect(
      page.getByRole("link", { name: "Create Character" })
    ).toBeVisible();
  });

  test("Create New button links to /characters/new", async ({ page }) => {
    await mockCharacterEndpoints(page);
    await page.goto("/characters");
    await page.waitForLoadState("networkidle");

    const createLink = page.getByRole("link", { name: /Create New/ });
    await expect(createLink).toBeVisible();
    await expect(createLink).toHaveAttribute("href", "/characters/new");
  });

  // -----------------------------------------------------------------------
  // Create character form
  // -----------------------------------------------------------------------

  test("create character form renders with entity type selector", async ({
    page,
  }) => {
    await mockCharacterEndpoints(page);
    await page.goto("/characters/new");
    await page.waitForLoadState("networkidle");

    await expect(
      page.getByRole("heading", { name: "Create Character" })
    ).toBeVisible();
    await expect(page.locator("#name")).toBeVisible();
    await expect(page.locator("#description")).toBeVisible();
  });

  test("create person character submits and redirects", async ({ page }) => {
    await mockCharacterEndpoints(page);
    await page.goto("/characters/new");
    await page.waitForLoadState("networkidle");

    // Use click + pressSequentially for reliable React state sync
    const nameInput = page.locator("#name");
    await nameInput.click();
    await nameInput.pressSequentially("Elena Voss");

    await page.locator("#description").fill("A cyberpunk detective");

    // Person fields should be visible by default
    await expect(page.getByText("Gender")).toBeVisible();
    await expect(page.getByText("Age Range")).toBeVisible();
    await expect(page.getByText("Build")).toBeVisible();

    // Wait for button to be enabled then submit
    const submitBtn = page.getByRole("button", { name: "Create Character" });
    await expect(submitBtn).toBeEnabled({ timeout: 5_000 });
    await submitBtn.click();

    await expect(page).toHaveURL(/\/characters$/, { timeout: 10_000 });
  });

  test("switching to environment entity shows environment-specific fields", async ({
    page,
  }) => {
    await mockCharacterEndpoints(page);
    await page.goto("/characters/new");
    await page.waitForLoadState("networkidle");

    await selectEntityType(page, "environment");

    // Person-specific fields should be hidden
    await expect(page.getByText("Gender")).not.toBeVisible();

    // Environment-specific fields should appear
    await expect(page.locator("#lighting")).toBeVisible();
    await expect(page.locator("#atmosphere")).toBeVisible();
    await expect(page.locator("#time_of_day")).toBeVisible();
    await expect(page.locator("#arch_style")).toBeVisible();
  });

  test("create environment character submits successfully", async ({
    page,
  }) => {
    await mockCharacterEndpoints(page);
    await page.goto("/characters/new");
    await page.waitForLoadState("networkidle");

    await selectEntityType(page, "environment");

    // Fill form — use pressSequentially for name (React controlled)
    const nameInput = page.locator("#name");
    await nameInput.click();
    await nameInput.pressSequentially("Neon Alley");

    await page.locator("#description").fill("A rain-soaked cyberpunk alley");
    await page.locator("#lighting").fill("neon-lit, reflective puddles");
    await page.locator("#atmosphere").fill("dense fog, humid");
    await page.locator("#time_of_day").fill("midnight");
    await page.locator("#arch_style").fill("cyberpunk brutalist");

    const submitBtn = page.getByRole("button", { name: "Create Character" });
    await expect(submitBtn).toBeEnabled({ timeout: 5_000 });
    await submitBtn.click();

    await expect(page).toHaveURL(/\/characters$/, { timeout: 10_000 });
  });

  // -----------------------------------------------------------------------
  // Delete character
  // -----------------------------------------------------------------------

  test("delete character shows confirmation dialog", async ({ page }) => {
    await mockCharacterEndpoints(page);
    await page.goto("/characters");
    await page.waitForLoadState("networkidle");

    await expect(page.getByText(mockCharacter.name)).toBeVisible({
      timeout: 10_000,
    });

    await page.getByLabel("Character actions").click();
    await page.getByRole("menuitem", { name: "Delete" }).click();

    await expect(page.getByText("Delete character")).toBeVisible();
    await expect(
      page.getByText("This action cannot be undone")
    ).toBeVisible();
  });

  // -----------------------------------------------------------------------
  // Cancel / Back navigation
  // -----------------------------------------------------------------------

  test("cancel on create form links back to character list", async ({
    page,
  }) => {
    await mockCharacterEndpoints(page);
    await page.goto("/characters/new");
    await page.waitForLoadState("networkidle");

    // Verify Cancel link is present and points to /characters
    const cancelLink = page.getByRole("link", { name: "Cancel" });
    await expect(cancelLink).toBeVisible();
    await expect(cancelLink).toHaveAttribute("href", "/characters");
  });
});
