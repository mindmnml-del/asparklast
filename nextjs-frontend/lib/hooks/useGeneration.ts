"use client";

import { useMutation } from "@tanstack/react-query";
import {
  generatePrompt,
  type AutoGenerateResponse,
} from "@/lib/api/generation";
import { useGenerationStore } from "@/store/generationStore";
import { ApiError } from "@/lib/api/client";
import type { GenerationRequest } from "@/lib/types/api";

export function useGeneration() {
  const { startGeneration, finishGeneration, setError, clearError } =
    useGenerationStore();

  return useMutation<AutoGenerateResponse, ApiError, GenerationRequest>({
    mutationFn: async (request: GenerationRequest) => {
      clearError();
      const controller = startGeneration();
      return generatePrompt(request, controller.signal);
    },
    onSuccess: () => {
      finishGeneration();
    },
    onError: (error: ApiError) => {
      finishGeneration();

      if (error.message === "canceled" || error.name === "CanceledError") {
        return;
      }

      if (error.isCreditsError) {
        setError(
          error.detail || "Insufficient Sparks. Your prompt has been saved.",
          true
        );
      } else {
        setError(error.detail || "Generation failed. Please try again.", false);
      }
    },
  });
}
