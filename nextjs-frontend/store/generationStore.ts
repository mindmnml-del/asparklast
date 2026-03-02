"use client";

import { create } from "zustand";

interface GenerationState {
  isGenerating: boolean;
  elapsedSeconds: number;
  abortController: AbortController | null;
  error: string | null;
  isCreditsError: boolean;

  startGeneration: () => AbortController;
  cancelGeneration: () => void;
  finishGeneration: () => void;
  tick: () => void;
  setError: (message: string, isCredits: boolean) => void;
  clearError: () => void;
}

export const useGenerationStore = create<GenerationState>((set, get) => ({
  isGenerating: false,
  elapsedSeconds: 0,
  abortController: null,
  error: null,
  isCreditsError: false,

  startGeneration: () => {
    const prev = get().abortController;
    if (prev) prev.abort();

    const controller = new AbortController();
    set({
      abortController: controller,
      isGenerating: true,
      elapsedSeconds: 0,
      error: null,
      isCreditsError: false,
    });
    return controller;
  },

  cancelGeneration: () => {
    const controller = get().abortController;
    if (controller) controller.abort();
    set({ isGenerating: false });
  },

  finishGeneration: () => {
    set({
      isGenerating: false,
      abortController: null,
    });
  },

  tick: () => {
    set((state) => ({ elapsedSeconds: state.elapsedSeconds + 1 }));
  },

  setError: (message: string, isCredits: boolean) => {
    set({ error: message, isCreditsError: isCredits });
  },

  clearError: () => {
    set({ error: null, isCreditsError: false });
  },
}));
