import apiClient from "@/lib/api/client";
import type { CriticAnalysisRequest, CriticAnalysis } from "@/lib/types/api";

export async function analyzeCritic(
  request: CriticAnalysisRequest
): Promise<CriticAnalysis> {
  const { data } = await apiClient.post<CriticAnalysis>(
    "/critic/analyze",
    request
  );
  return data;
}
