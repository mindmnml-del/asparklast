import { test, expect } from "@playwright/test";
import {
  mockAuthEndpoints,
  mockCharacterEndpoints,
  injectAuthState,
} from "../helpers/api-mocks";

test.describe("Authentication", () => {
  // -----------------------------------------------------------------------
  // Login page
  // -----------------------------------------------------------------------

  test("renders login page with email and password inputs", async ({ page }) => {
    await page.goto("/login");
    await expect(page.locator("#email")).toBeVisible();
    await expect(page.locator("#password")).toBeVisible();
    await expect(page.getByRole("button", { name: "Sign In" })).toBeVisible();
  });

  test("successful login redirects to /generate", async ({ page }) => {
    await mockAuthEndpoints(page);
    await page.goto("/login");

    await page.locator("#email").fill("test@aispark.studio");
    await page.locator("#password").fill("Password123!");
    await page.getByRole("button", { name: "Sign In" }).click();

    await expect(page).toHaveURL(/\/generate/, { timeout: 10_000 });
  });

  test("login error shows error banner", async ({ page }) => {
    // Use 400 (not 401) because the axios interceptor redirects on 401,
    // which causes a full page reload and loses the mutation error state.
    await mockAuthEndpoints(page, { loginStatus: 400 });
    await page.goto("/login");

    await page.locator("#email").fill("wrong@email.com");
    await page.locator("#password").fill("badpassword");
    await page.getByRole("button", { name: "Sign In" }).click();

    await expect(page.getByText("Invalid credentials")).toBeVisible({
      timeout: 5_000,
    });
  });

  test("navigate to register page", async ({ page }) => {
    await page.goto("/login");
    await page.waitForLoadState("networkidle");
    await page.getByRole("link", { name: "Create one" }).click();
    await expect(page).toHaveURL(/\/register/, { timeout: 10_000 });
  });

  // -----------------------------------------------------------------------
  // Register page
  // -----------------------------------------------------------------------

  test("renders register page with all fields", async ({ page }) => {
    await page.goto("/register");
    await expect(page.locator("#fullName")).toBeVisible();
    await expect(page.locator("#reg-email")).toBeVisible();
    await expect(page.locator("#reg-password")).toBeVisible();
    await expect(
      page.getByRole("button", { name: "Create Account" })
    ).toBeVisible();
  });

  test("password strength indicators update on input", async ({ page }) => {
    await page.goto("/register");
    await page.waitForLoadState("networkidle");

    // Type a weak password — only lowercase
    const pwInput = page.locator("#reg-password");
    await pwInput.click();
    await pwInput.pressSequentially("abc");

    // Indicators should appear after typing
    await expect(page.getByText("8+ characters")).toBeVisible();
    await expect(page.getByText("Lowercase")).toBeVisible();

    // Type a strong password
    await pwInput.fill("");
    await pwInput.pressSequentially("Str0ng!Pass");

    // "8+ characters" indicator should now have emerald (passing) style
    const indicator = page.getByText("8+ characters");
    await expect(indicator).toHaveClass(/emerald/, { timeout: 3_000 });
  });

  test("successful registration redirects to /generate", async ({ page }) => {
    await mockAuthEndpoints(page);
    await page.goto("/register");
    await page.waitForLoadState("networkidle");

    await page.locator("#fullName").fill("Test User");
    await page.locator("#reg-email").fill("new@aispark.studio");

    // Use pressSequentially for password to trigger React state + strength validation
    const pwInput = page.locator("#reg-password");
    await pwInput.click();
    await pwInput.pressSequentially("Str0ng!Pass");

    await page.getByRole("button", { name: "Create Account" }).click();

    await expect(page).toHaveURL(/\/generate/, { timeout: 10_000 });
  });

  test("navigate from register to login", async ({ page }) => {
    await page.goto("/register");
    await page.getByRole("link", { name: "Sign in" }).click();
    await expect(page).toHaveURL(/\/login/);
  });

  // -----------------------------------------------------------------------
  // Sign out
  // -----------------------------------------------------------------------

  test("sign out redirects to login", async ({ page }) => {
    await injectAuthState(page);
    await mockAuthEndpoints(page);
    await mockCharacterEndpoints(page);
    await page.goto("/generate");
    await page.waitForLoadState("networkidle");

    // Click user avatar button (aria-label="User menu")
    await page.getByLabel("User menu").click();

    // Wait for dropdown to fully render, then click sign out
    const signOutBtn = page.getByText("Sign out");
    await expect(signOutBtn).toBeVisible({ timeout: 3_000 });
    await signOutBtn.click();

    await expect(page).toHaveURL(/\/login/, { timeout: 10_000 });
  });
});
