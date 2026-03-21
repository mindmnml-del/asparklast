"use client";

import { create } from "zustand";
import type { User } from "@/lib/types/api";

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  credits: number;

  setUser: (user: User) => void;
  loginSuccess: (user: User) => void;
  clearAuth: () => void;
  setLoading: (loading: boolean) => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,
  isLoading: false,
  credits: 0,

  setUser: (user: User) =>
    set({
      user,
      isAuthenticated: true,
      credits: user.credits,
    }),

  loginSuccess: (user: User) => {
    set({
      user,
      isAuthenticated: true,
      credits: user.credits,
    });
  },

  clearAuth: () => {
    set({
      user: null,
      isAuthenticated: false,
      credits: 0,
    });
  },

  setLoading: (loading: boolean) =>
    set({ isLoading: loading }),
}));
