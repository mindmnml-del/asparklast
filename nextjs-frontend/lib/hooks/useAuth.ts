"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { loginUser, registerUser, getCurrentUser } from "@/lib/api/auth";
import { useAuthStore } from "@/store/authStore";
import apiClient, { ApiError } from "@/lib/api/client";
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
      // Backend sets httpOnly cookie via Set-Cookie header
      const token = await loginUser(email, password);
      const user = await getCurrentUser();
      return { token, user };
    },
    onSuccess: ({ user }) => {
      loginSuccess(user);
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
      // Auto-login after registration — backend sets httpOnly cookie
      const token = await loginUser(payload.email, payload.password);
      const freshUser = await getCurrentUser();
      return { token, user: freshUser ?? user };
    },
    onSuccess: ({ user }) => {
      loginSuccess(user);
      queryClient.invalidateQueries({ queryKey: USER_QUERY_KEY });
      router.push("/generate");
    },
  });

  // --- Logout ---
  const logout = async () => {
    await apiClient.post("/auth/logout").catch(() => {});
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
