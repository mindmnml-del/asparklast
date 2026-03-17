"use client";

import { useMutation } from "@tanstack/react-query";
import { analyzeCritic } from "@/lib/api/critic";
import type { ApiError } from "@/lib/api/client";
import type { CriticAnalysisRequest, CriticAnalysis } from "@/lib/types/api";

export function useCritic() {
  return useMutation<CriticAnalysis, ApiError, CriticAnalysisRequest>({
    mutationFn: analyzeCritic,
  });
}
