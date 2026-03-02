"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { loginUser, registerUser, getCurrentUser } from "@/lib/api/auth";
import { useAuthStore } from "@/store/authStore";
import { setToken, ApiError } from "@/lib/api/client";
import type { UserCreate, User, Token } from "@/lib/types/api";

const USER_QUERY_KEY = ["currentUser"] as const;

export function useAuth() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const { loginSuccess, clearAuth } = useAuthStore();

  // --- Login mutation ---
  const loginMutation = useMutation<
    { token: Token; user: User },
    ApiError,
    { email: string; password: string }
  >({
    mutationFn: async ({ email, password }) => {
      const token = await loginUser(email, password);
      // Set cookie so the interceptor picks it up for the next call
      setToken(token.access_token);
      const user = await getCurrentUser();
      return { token, user };
    },
    onSuccess: ({ token, user }) => {
      loginSuccess(token.access_token, user);
      queryClient.invalidateQueries({ queryKey: USER_QUERY_KEY });
      router.push("/generate");
    },
  });

  // --- Register mutation ---
  const registerMutation = useMutation<
    { token: Token; user: User },
    ApiError,
    UserCreate
  >({
    mutationFn: async (payload) => {
      const user = await registerUser(payload);
      // Auto-login after registration
      const token = await loginUser(payload.email, payload.password);
      setToken(token.access_token);
      // Re-fetch user to ensure fresh data
      const freshUser = await getCurrentUser();
      return { token, user: freshUser ?? user };
    },
    onSuccess: ({ token, user }) => {
      loginSuccess(token.access_token, user);
      queryClient.invalidateQueries({ queryKey: USER_QUERY_KEY });
      router.push("/generate");
    },
  });

  // --- Logout ---
  const logout = () => {
    clearAuth();
    queryClient.removeQueries({ queryKey: USER_QUERY_KEY });
    router.push("/login");
  };

  return {
    login: loginMutation.mutate,
    isLoggingIn: loginMutation.isPending,
    loginError: loginMutation.error,

    register: registerMutation.mutate,
    isRegistering: registerMutation.isPending,
    registerError: registerMutation.error,

    logout,
  };
}
