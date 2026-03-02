import apiClient from "@/lib/api/client";
import type { GenerationRequest, PromptStructure } from "@/lib/types/api";

export interface AutoGenerateResponse {
  structuredPrompt: PromptStructure;
  paragraphPrompt: string;
  negativePrompt: string;
  tool: string;
  type: string;
  _metadata?: Record<string, unknown>;
  id?: number;
  created_at?: string;
}

export async function generatePrompt(
  request: GenerationRequest,
  signal?: AbortSignal
): Promise<AutoGenerateResponse> {
  const { data } = await apiClient.post<AutoGenerateResponse>(
    "/helios/auto-generate",
    request,
    { signal }
  );
  return data;
}
