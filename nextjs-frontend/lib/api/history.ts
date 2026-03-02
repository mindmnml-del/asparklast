import apiClient from "@/lib/api/client";
import type { GeneratedPromptHistory, GeneratedPrompt } from "@/lib/types/api";

export interface GetPromptsParams {
  skip?: number;
  limit?: number;
  favorites_only?: boolean;
}

/** GET /prompts — paginated list of user's prompts. */
export async function getPrompts(
  params?: GetPromptsParams
): Promise<GeneratedPromptHistory[]> {
  const { data } = await apiClient.get<GeneratedPromptHistory[]>("/prompts", {
    params,
  });
  return data;
}

/** GET /prompts/{id} — full prompt with raw_response and feedback. */
export async function getPromptById(id: number): Promise<GeneratedPrompt> {
  const { data } = await apiClient.get<GeneratedPrompt>(`/prompts/${id}`);
  return data;
}

/** PUT /prompts/{id}/favorite — toggle favorite status. */
export async function toggleFavorite(
  id: number,
  is_favorite: boolean
): Promise<GeneratedPrompt> {
  const { data } = await apiClient.put<GeneratedPrompt>(
    `/prompts/${id}/favorite`,
    null,
    { params: { is_favorite } }
  );
  return data;
}

/** DELETE /prompts/{id} — delete a prompt. */
export async function deletePrompt(
  id: number
): Promise<{ success: boolean }> {
  const { data } = await apiClient.delete<{ success: boolean }>(
    `/prompts/${id}`
  );
  return data;
}
