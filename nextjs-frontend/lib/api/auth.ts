import apiClient from "@/lib/api/client";
import type { User, Token, UserCreate } from "@/lib/types/api";

/**
 * POST /auth/token — OAuth2 form-urlencoded login.
 * FastAPI's OAuth2PasswordRequestForm expects `username` and `password` fields.
 */
export async function loginUser(
  email: string,
  password: string
): Promise<Token> {
  const params = new URLSearchParams();
  params.append("username", email);
  params.append("password", password);

  const { data } = await apiClient.post<Token>("/auth/token", params, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });
  return data;
}

/** POST /auth/register — JSON body registration. */
export async function registerUser(payload: UserCreate): Promise<User> {
  const { data } = await apiClient.post<User>("/auth/register", payload);
  return data;
}

/** GET /users/me — Bearer token injected by the client interceptor. */
export async function getCurrentUser(): Promise<User> {
  const { data } = await apiClient.get<User>("/users/me");
  return data;
}
