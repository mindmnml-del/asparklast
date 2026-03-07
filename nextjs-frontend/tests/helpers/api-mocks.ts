import type { Page } from "@playwright/test";
import {
  mockUser,
  mockToken,
  mockAIResponse,
  mockCharacterList,
  mockCriticAnalysis,
  mockExtractionResponse,
} from "./mock-data";

// Backend API base URL used by the axios client
const API_BASE = "http://localhost:8001";

// ---------------------------------------------------------------------------
// Auth mocks
// ---------------------------------------------------------------------------

export async function mockAuthEndpoints(
  page: Page,
  opts?: { loginStatus?: number; registerStatus?: number }
) {
  const loginStatus = opts?.loginStatus ?? 200;
  const registerStatus = opts?.registerStatus ?? 200;

  // POST /auth/token (login — form-urlencoded)
  await page.route(`${API_BASE}/auth/token`, (route) => {
    if (loginStatus !== 200) {
      return route.fulfill({
        status: loginStatus,
        contentType: "application/json",
        body: JSON.stringify({ detail: "Invalid credentials" }),
      });
    }
    return route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(mockToken),
    });
  });

  // POST /auth/register
  await page.route(`${API_BASE}/auth/register`, (route) => {
    if (registerStatus !== 200) {
      return route.fulfill({
        status: registerStatus,
        contentType: "application/json",
        body: JSON.stringify({ detail: "Email already registered" }),
      });
    }
    return route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(mockUser),
    });
  });

  // GET /users/me
  await page.route(`${API_BASE}/users/me`, (route) => {
    return route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(mockUser),
    });
  });
}

// ---------------------------------------------------------------------------
// Generation mocks
// ---------------------------------------------------------------------------

export async function mockGenerationEndpoints(
  page: Page,
  opts?: { delayMs?: number; status?: number }
) {
  const delayMs = opts?.delayMs ?? 500;
  const status = opts?.status ?? 200;

  // POST /helios/auto-generate
  await page.route(`${API_BASE}/helios/auto-generate`, async (route) => {
    if (delayMs > 0) {
      await new Promise((r) => setTimeout(r, delayMs));
    }

    if (status !== 200) {
      const detail =
        status === 402
          ? "Insufficient credits"
          : "Internal server error";
      return route.fulfill({
        status,
        contentType: "application/json",
        body: JSON.stringify({ detail }),
      });
    }

    return route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(mockAIResponse),
    });
  });
}

// ---------------------------------------------------------------------------
// Character mocks
// ---------------------------------------------------------------------------

export async function mockCharacterEndpoints(
  page: Page,
  opts?: { emptyList?: boolean }
) {
  // GET /characters/list
  await page.route(`${API_BASE}/characters/list`, (route) => {
    if (opts?.emptyList) {
      return route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ success: true, characters: [], total: 0 }),
      });
    }
    return route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(mockCharacterList),
    });
  });

  // POST /characters/create
  await page.route(`${API_BASE}/characters/create`, (route) => {
    return route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        success: true,
        character: { ...mockCharacterList.characters[0], character_id: "new-char-001" },
        message: "Character created",
      }),
    });
  });

  // DELETE /characters/*
  await page.route(`${API_BASE}/characters/char-*`, (route) => {
    if (route.request().method() === "DELETE") {
      return route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ success: true }),
      });
    }
    // GET single character
    return route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        success: true,
        character: mockCharacterList.characters[0],
      }),
    });
  });

  // POST /characters/extract-from-prompt
  await page.route(`${API_BASE}/characters/extract-from-prompt`, (route) => {
    return route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(mockExtractionResponse),
    });
  });

  // GET /characters/session/current
  await page.route(`${API_BASE}/characters/session/current`, (route) => {
    return route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ success: true, character: null }),
    });
  });
}

// ---------------------------------------------------------------------------
// Critic mocks
// ---------------------------------------------------------------------------

export async function mockCriticEndpoints(page: Page) {
  await page.route(`${API_BASE}/critic/analyze`, (route) => {
    return route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(mockCriticAnalysis),
    });
  });
}

// ---------------------------------------------------------------------------
// Auth state injection — sets cookie + navigates so Zustand picks it up
// ---------------------------------------------------------------------------

export async function injectAuthState(page: Page) {
  // Set the auth cookie before navigating
  await page.context().addCookies([
    {
      name: "aispark_token",
      value: mockToken.access_token,
      domain: "localhost",
      path: "/",
      sameSite: "Strict",
    },
  ]);
}
